from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from math import log, sqrt
from statistics import stdev

from sqlalchemy.orm import Session

from oilify_studio_backend.db.schema import HistoricalVolatility, Price, TechnicalIndicator


logger = logging.getLogger(__name__)

SMA_WINDOW = 20
EMA_WINDOW = 20
RSI_WINDOW = 14
VOLATILITY_WINDOW = 20
ANNUALIZATION_FACTOR = 252


@dataclass(frozen=True)
class PriceSeriesPoint:
    price_date: date
    price: float


@dataclass(frozen=True)
class RecalculatedAnalytics:
    indicator_rows: list[TechnicalIndicator]
    volatility_rows: list[HistoricalVolatility]


def _group_price_rows(db: Session) -> dict[int, list[PriceSeriesPoint]]:
    """Group prices by ticker, aggregated to daily (last price of each day)."""
    raw_rows = (
        db.query(Price)
        .order_by(Price.ticker_id, Price.price_at, Price.id)
        .all()
    )
    daily: dict[int, dict[date, float]] = defaultdict(dict)
    for row in raw_rows:
        daily[row.ticker_id][row.price_at.date()] = row.price

    result: dict[int, list[PriceSeriesPoint]] = {}
    for ticker_id, day_map in daily.items():
        result[ticker_id] = [
            PriceSeriesPoint(price_date=d, price=p)
            for d, p in sorted(day_map.items())
        ]
    return result


def _build_sma_points(points: list[PriceSeriesPoint], window: int) -> list[tuple[date, float]]:
    if len(points) < window:
        return []

    results: list[tuple[date, float]] = []
    rolling_total = sum(point.price for point in points[:window])
    results.append((points[window - 1].price_date, rolling_total / window))

    for index in range(window, len(points)):
        rolling_total += points[index].price - points[index - window].price
        results.append((points[index].price_date, rolling_total / window))

    return results


def _build_ema_points(points: list[PriceSeriesPoint], window: int) -> list[tuple[date, float]]:
    if not points:
        return []

    multiplier = 2 / (window + 1)
    ema_value = points[0].price
    results: list[tuple[date, float]] = [(points[0].price_date, ema_value)]

    for point in points[1:]:
        ema_value = (point.price - ema_value) * multiplier + ema_value
        results.append((point.price_date, ema_value))

    return results


def _build_rsi_points(points: list[PriceSeriesPoint], window: int) -> list[tuple[date, float]]:
    if len(points) <= window:
        return []

    gains = 0.0
    losses = 0.0
    for index in range(1, window + 1):
        delta = points[index].price - points[index - 1].price
        gains += max(delta, 0.0)
        losses += max(-delta, 0.0)

    average_gain = gains / window
    average_loss = losses / window
    results: list[tuple[date, float]] = []

    def _calculate_rsi(gain_value: float, loss_value: float) -> float:
        if loss_value == 0:
            return 100.0
        relative_strength = gain_value / loss_value
        return 100.0 - (100.0 / (1.0 + relative_strength))

    results.append((points[window].price_date, _calculate_rsi(average_gain, average_loss)))

    for index in range(window + 1, len(points)):
        delta = points[index].price - points[index - 1].price
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        average_gain = ((average_gain * (window - 1)) + gain) / window
        average_loss = ((average_loss * (window - 1)) + loss) / window
        results.append((points[index].price_date, _calculate_rsi(average_gain, average_loss)))

    return results


def _build_historical_volatility_points(
    points: list[PriceSeriesPoint],
    window: int,
    annualization_factor: int,
) -> list[tuple[date, float]]:
    if len(points) <= window:
        return []

    returns: list[float] = []
    for index in range(1, len(points)):
        previous_price = points[index - 1].price
        current_price = points[index].price
        if previous_price <= 0 or current_price <= 0:
            continue
        returns.append(log(current_price / previous_price))

    if len(returns) < window:
        return []

    volatility_points: list[tuple[date, float]] = []
    for end_index in range(window, len(returns) + 1):
        window_returns = returns[end_index - window : end_index]
        if len(window_returns) < 2:
            continue
        volatility = stdev(window_returns) * sqrt(annualization_factor)
        volatility_points.append((points[end_index].price_date, volatility))

    return volatility_points


def rebuild_market_analytics(db: Session) -> RecalculatedAnalytics:
    logger.info("Rebuilding derived market analytics")
    db.query(TechnicalIndicator).delete(synchronize_session=False)
    db.query(HistoricalVolatility).delete(synchronize_session=False)
    db.flush()

    grouped_rows = _group_price_rows(db)
    indicator_rows: list[TechnicalIndicator] = []
    volatility_rows: list[HistoricalVolatility] = []

    for ticker_id, points in grouped_rows.items():
        sma_points = _build_sma_points(points, SMA_WINDOW)
        ema_points = _build_ema_points(points, EMA_WINDOW)
        rsi_points = _build_rsi_points(points, RSI_WINDOW)
        volatility_points = _build_historical_volatility_points(
            points,
            VOLATILITY_WINDOW,
            ANNUALIZATION_FACTOR,
        )

        indicator_rows.extend(
            TechnicalIndicator(
                ticker_id=ticker_id,
                date=indicator_date,
                name="sma_20",
                value=indicator_value,
                window_size=SMA_WINDOW,
            )
            for indicator_date, indicator_value in sma_points
        )
        indicator_rows.extend(
            TechnicalIndicator(
                ticker_id=ticker_id,
                date=indicator_date,
                name="ema_20",
                value=indicator_value,
                window_size=EMA_WINDOW,
            )
            for indicator_date, indicator_value in ema_points
        )
        indicator_rows.extend(
            TechnicalIndicator(
                ticker_id=ticker_id,
                date=indicator_date,
                name="rsi_14",
                value=indicator_value,
                window_size=RSI_WINDOW,
            )
            for indicator_date, indicator_value in rsi_points
        )
        volatility_rows.extend(
            HistoricalVolatility(
                ticker_id=ticker_id,
                date=volatility_date,
                value=volatility_value,
                window_size=VOLATILITY_WINDOW,
                annualization_factor=ANNUALIZATION_FACTOR,
            )
            for volatility_date, volatility_value in volatility_points
        )

    db.add_all(indicator_rows)
    db.add_all(volatility_rows)
    db.commit()

    logger.info(
        "Rebuilt market analytics indicators=%s volatility=%s",
        len(indicator_rows),
        len(volatility_rows),
    )
    return RecalculatedAnalytics(indicator_rows=indicator_rows, volatility_rows=volatility_rows)
