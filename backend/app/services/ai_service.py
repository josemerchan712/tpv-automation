from datetime import date, datetime, time, timezone, timedelta
from decimal import Decimal

import google.generativeai as genai
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.product import Product
from app.models.sale import Sale, SaleItem


def _gather_weekly_data(db: Session) -> dict:
    today = date.today()
    week_start = today - timedelta(days=6)
    prev_week_start = today - timedelta(days=13)
    prev_week_end = today - timedelta(days=7)

    def sales_in_range(start: date, end: date) -> list[Sale]:
        dt_start = datetime.combine(start, time.min).replace(tzinfo=timezone.utc)
        dt_end = datetime.combine(end, time.max).replace(tzinfo=timezone.utc)
        return db.query(Sale).filter(Sale.fecha >= dt_start, Sale.fecha <= dt_end).all()

    current_sales = sales_in_range(week_start, today)
    prev_sales = sales_in_range(prev_week_start, prev_week_end)

    daily: dict[str, dict] = {}
    for s in current_sales:
        d = s.fecha.date().isoformat()
        if d not in daily:
            daily[d] = {"total": Decimal("0"), "tickets": 0}
        daily[d]["total"] += s.total
        daily[d]["tickets"] += 1

    dt_week_start = datetime.combine(week_start, time.min).replace(tzinfo=timezone.utc)
    dt_today_end = datetime.combine(today, time.max).replace(tzinfo=timezone.utc)
    top_rows = (
        db.query(
            Product.nombre,
            func.sum(SaleItem.cantidad).label("cantidad"),
            func.sum(SaleItem.cantidad * SaleItem.precio_unitario).label("importe"),
        )
        .join(SaleItem, Product.id == SaleItem.product_id)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(Sale.fecha >= dt_week_start, Sale.fecha <= dt_today_end)
        .group_by(Product.nombre)
        .order_by(func.sum(SaleItem.cantidad).desc())
        .limit(5)
        .all()
    )

    current_total = sum((s.total for s in current_sales), Decimal("0"))
    prev_total = sum((s.total for s in prev_sales), Decimal("0"))

    return {
        "periodo": f"{week_start.isoformat()} al {today.isoformat()}",
        "total_actual": float(current_total),
        "total_semana_anterior": float(prev_total),
        "num_tickets": len(current_sales),
        "ventas_diarias": {
            d: {"total": float(v["total"]), "tickets": v["tickets"]}
            for d, v in sorted(daily.items())
        },
        "top_productos": [
            {"nombre": r.nombre, "cantidad": r.cantidad, "importe": float(r.importe)}
            for r in top_rows
        ],
    }


def _gather_stock_data(db: Session) -> dict:
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)

    products = db.query(Product).order_by(Product.nombre).all()

    def units_sold_since(product_id: int, since: date) -> int:
        dt_since = datetime.combine(since, time.min).replace(tzinfo=timezone.utc)
        result = (
            db.query(func.sum(SaleItem.cantidad))
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(SaleItem.product_id == product_id, Sale.fecha >= dt_since)
            .scalar()
        )
        return result or 0

    product_data = []
    for p in products:
        sold_30 = units_sold_since(p.id, thirty_days_ago)
        sold_60 = units_sold_since(p.id, sixty_days_ago)
        product_data.append({
            "nombre": p.nombre,
            "stock_actual": p.stock,
            "stock_minimo": p.stock_minimo,
            "vendidas_30d": sold_30,
            "vendidas_60d": sold_60,
        })

    return {
        "fecha_analisis": today.isoformat(),
        "productos": product_data,
    }


def _get_model() -> genai.GenerativeModel:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="IA no configurada: falta la variable de entorno GEMINI_API_KEY",
        )
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


def generate_weekly_report(db: Session) -> str:
    model = _get_model()
    data = _gather_weekly_data(db)

    if data["total_semana_anterior"] > 0:
        variacion = (data["total_actual"] - data["total_semana_anterior"]) / data["total_semana_anterior"] * 100
    else:
        variacion = 0.0

    ventas_str = "\n".join(
        f"  {d}: {v['total']:.2f}€ ({v['tickets']} tickets)"
        for d, v in data["ventas_diarias"].items()
    ) or "  Sin ventas registradas"

    top_str = "\n".join(
        f"  {i + 1}. {p['nombre']}: {p['cantidad']} uds — {p['importe']:.2f}€"
        for i, p in enumerate(data["top_productos"])
    ) or "  Sin ventas registradas"

    prompt = f"""Eres el analista de negocio de un punto de venta (TPV) en España. \
Analiza los datos de ventas de la semana y responde ÚNICAMENTE en español con un informe ejecutivo estructurado.

DATOS DE LA SEMANA ({data['periodo']}):
- Total facturado esta semana: {data['total_actual']:.2f}€
- Total semana anterior: {data['total_semana_anterior']:.2f}€
- Variación respecto a semana anterior: {variacion:+.1f}%
- Número de tickets: {data['num_tickets']}

VENTAS POR DÍA:
{ventas_str}

TOP 5 PRODUCTOS (por unidades vendidas):
{top_str}

Genera un informe ejecutivo con estas secciones claramente delimitadas:
1. **Resumen de la semana** (2-3 frases)
2. **Tendencias destacadas**
3. **Anomalías o puntos de atención** (si no hay, indícalo)
4. **Recomendaciones concretas para la próxima semana**
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al contactar con la IA: {exc}",
        )


def generate_stock_analysis(db: Session) -> str:
    model = _get_model()
    data = _gather_stock_data(db)

    productos_str = "\n".join(
        f"  - {p['nombre']}: stock {p['stock_actual']} (mín {p['stock_minimo']}) | "
        f"vendidas 30d: {p['vendidas_30d']} | vendidas 60d: {p['vendidas_60d']}"
        for p in data["productos"]
    ) or "  Sin productos registrados"

    prompt = f"""Eres el gestor de inventario de un punto de venta (TPV) en España. \
Analiza los datos de stock y ventas y responde ÚNICAMENTE en español.

FECHA DE ANÁLISIS: {data['fecha_analisis']}
TOTAL DE PRODUCTOS: {len(data['productos'])}

DATOS POR PRODUCTO (stock actual | mínimo | vendidas en últimos 30d | vendidas en últimos 60d):
{productos_str}

Genera un análisis con estas secciones claramente delimitadas:
1. **Estado general del inventario**
2. **Alta rotación** — productos que venden bien y podrían necesitar mayor stock_minimo
3. **Sin movimiento o baja rotación** — productos con 0 ventas en 60 días (revisar si mantener)
4. **Ajustes de stock_minimo sugeridos** — lista concreta: Producto → valor actual → valor sugerido
5. **Reposición urgente** — productos con stock actual por debajo del mínimo
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Error al contactar con la IA: {exc}",
        )
