from sqlmodel import SQLModel


class StatsOverview(SQLModel):
    total: int
    mastered: int
    learning: int
    new_count: int
    mastered_percent: float


class StatsByGrade(SQLModel):
    grade: int
    semester: int
    total: int
    mastered: int
    learning: int
    new_count: int
    mastered_percent: float
