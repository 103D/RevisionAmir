from fastapi import APIRouter, HTTPException

try:
    from .redis_holidays_store import RedisHolidaysStore
except ImportError:
    from redis_holidays_store import RedisHolidaysStore

router = APIRouter()

holidays_store = RedisHolidaysStore()


@router.get("/holidays")
async def get_all_holidays():
    return holidays_store.get_all_holidays()


@router.get("/holidays/{year}")
async def get_holidays_by_year(year: str):
    all_holidays = holidays_store.get_all_holidays()
    year_holidays = [h for h in all_holidays if h.get("date", "").startswith(year)]
    if year_holidays:
        return year_holidays
    else:
        return []


@router.post("/holidays")
async def add_holiday(holiday_data: dict):
    if "date" not in holiday_data or "name" not in holiday_data:
        raise HTTPException(status_code=400, detail="Holiday must have 'date' and 'name' fields")

    holidays_store.add_holiday(holiday_data)
    return {"message": "Holiday added successfully", "holiday": holiday_data}


@router.put("/holidays/{id}")
async def update_holiday(id: str, holiday_data: dict):
    if "date" not in holiday_data or "name" not in holiday_data:
        raise HTTPException(status_code=400, detail="Holiday must have 'date' and 'name' fields")

    updated = holidays_store.update_holiday(id, holiday_data)
    if updated:
        return {"message": "Holiday updated successfully", "holiday": holiday_data}
    raise HTTPException(status_code=404, detail="Holiday not found")


@router.delete("/holidays/{id}")
async def delete_holiday(id: str):
    deleted = holidays_store.delete_holiday(id)
    if deleted:
        return {"message": "Holiday deleted successfully"}
    raise HTTPException(status_code=404, detail="Holiday not found")