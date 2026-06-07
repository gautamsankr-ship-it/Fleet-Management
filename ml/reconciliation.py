import asyncio
import difflib
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import BankTransaction, DailyLogSheet, TransactionReconciliation


def _text_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _score_pair(tx: Any, sheet: Any) -> Decimal:
    amount_delta = abs(tx.amount - sheet.gross_collection)
    days_delta = abs((tx.transaction_date - sheet.date_gregorian).days)
    desc_similarity = _text_similarity(tx.narration, f'{sheet.vehicle_id} {sheet.driver_id} {sheet.conductor_id}')
    vehicle_bonus = 1.0 if getattr(sheet, 'vehicle_id', None) == getattr(tx, 'vehicle_id', None) else 0.0

    amount_score = max(0.0, 1.0 - float(amount_delta) / max(float(tx.amount or Decimal('1.00')), 5000.0))
    date_score = max(0.0, 1.0 - days_delta / 7.0)

    raw = (0.45 * amount_score) + (0.25 * date_score) + (0.20 * desc_similarity) + (0.10 * vehicle_bonus)
    return Decimal(str(min(raw, 1.0)))


async def match_transactions(db: AsyncSession, tenant_id: int, threshold: float = 0.65) -> list[dict[str, Any]]:
    bank_stmt = select(BankTransaction).where(BankTransaction.tenant_id == tenant_id, BankTransaction.matched == 0)
    bank_result = await db.execute(bank_stmt)
    bank_items = bank_result.scalars().all()

    sheet_stmt = select(DailyLogSheet).where(DailyLogSheet.tenant_id == tenant_id)
    sheet_result = await db.execute(sheet_stmt)
    sheet_items = sheet_result.scalars().all()

    matches: list[dict[str, Any]] = []
    for bank_tx in bank_items:
        candidates = []
        for sheet in sheet_items:
            amount_delta = abs(bank_tx.amount - sheet.gross_collection)
            date_delta = abs((bank_tx.transaction_date - sheet.date_gregorian).days)
            if amount_delta <= Decimal('20000.00') and date_delta <= 10:
                score = _score_pair(bank_tx, sheet)
                candidates.append((score, sheet))

        if not candidates:
            continue

        best_score, best_sheet = max(candidates, key=lambda item: item[0])
        if best_score >= Decimal(str(threshold)):
            matched_record = TransactionReconciliation(
                tenant_id=tenant_id,
                bank_transaction_id=bank_tx.id,
                daily_log_sheet_id=best_sheet.id,
                confidence_score=best_score,
                matched_by='automated_ml',
            )
            db.add(matched_record)
            bank_tx.matched = 1
            matches.append({
                'bank_transaction_id': bank_tx.id,
                'daily_log_sheet_id': best_sheet.id,
                'confidence_score': str(best_score),
            })

    if matches:
        await db.commit()
    return matches


if __name__ == '__main__':
    import os

    async def main() -> None:
        from db import async_session

        tenant_id = int(os.environ.get('TENANT_ID', '1'))
        async with async_session() as session:
            results = await match_transactions(session, tenant_id)
            print({'tenant_id': tenant_id, 'matched_count': len(results), 'results': results})

    asyncio.run(main())
