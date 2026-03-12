from typing import Iterable, List, Optional

from sqlalchemy import Select, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vacancy import Vacancy
from app.schemas.vacancy import VacancyCreate, VacancyUpdate


async def get_vacancy(session: AsyncSession, vacancy_id: int) -> Optional[Vacancy]:
    result = await session.execute(select(Vacancy).where(Vacancy.id == vacancy_id))
    return result.scalar_one_or_none()


async def get_vacancy_by_external_id(
    session: AsyncSession, external_id: int
) -> Optional[Vacancy]:
    result = await session.execute(
        select(Vacancy).where(Vacancy.external_id == external_id)
    )
    return result.scalar_one_or_none()


async def list_vacancies(
    session: AsyncSession,
    timetable_mode_name: Optional[str],
    city_name: Optional[str],
) -> List[Vacancy]:
    stmt: Select = select(Vacancy)
    if timetable_mode_name:
        stmt = stmt.where(Vacancy.timetable_mode_name.ilike(f"%{timetable_mode_name}%"))
    if city_name:
        stmt = stmt.where(Vacancy.city_name.ilike(f"%{city_name}%"))
    stmt = stmt.order_by(Vacancy.published_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_vacancy(session: AsyncSession, data: VacancyCreate) -> Vacancy:
    vacancy = Vacancy(**data.model_dump())
    session.add(vacancy)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


async def update_vacancy(
    session: AsyncSession, vacancy: Vacancy, data: VacancyUpdate
) -> Vacancy:
    for field, value in data.model_dump().items():
        setattr(vacancy, field, value)
    await session.commit()
    await session.refresh(vacancy)
    return vacancy


async def delete_vacancy(session: AsyncSession, vacancy: Vacancy) -> None:
    await session.delete(vacancy)
    await session.commit()


async def upsert_external_vacancies(
    session: AsyncSession, payloads: Iterable[dict]
) -> int:
    payloads = list(payloads)
    if not payloads:
        return 0

    with_external_id = [
        payload for payload in payloads if payload.get("external_id") is not None
    ]
    without_external_id = [
        payload for payload in payloads if payload.get("external_id") is None
    ]

    created_count = 0
    if with_external_id:
        insert_stmt = insert(Vacancy).values(with_external_id)
        excluded = insert_stmt.excluded
        update_columns = {
            "title": excluded.title,
            "timetable_mode_name": excluded.timetable_mode_name,
            "tag_name": excluded.tag_name,
            "city_name": excluded.city_name,
            "published_at": excluded.published_at,
            "is_remote_available": excluded.is_remote_available,
            "is_hot": excluded.is_hot,
        }
        upsert_stmt = (
            insert_stmt.on_conflict_do_update(
                index_elements=[Vacancy.external_id],
                set_=update_columns,
            )
            # xmax = 0 is true for freshly inserted rows
            .returning(text("(xmax = 0) AS inserted"))
        )
        result = await session.execute(upsert_stmt)
        created_count += sum(1 for row in result if row.inserted)

    for payload in without_external_id:
        session.add(Vacancy(**payload))
        created_count += 1

    await session.commit()
    return created_count
