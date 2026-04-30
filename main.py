from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import List, Optional
from enum import Enum


from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


app = FastAPI(
    title="Limkokwing Library API",

    description="A basic digital library system for managing books, borrows, and fines.",
    version="1.0.0",
)

class Category(str, Enum):
    fiction = "Fiction"
    science = "Science"
    technology = "Technology"
    history = "History"
    mathematics = "Mathematics"

class Book(BaseModel):
    book_id: int
    title: str
    author: str
    category: Category
    available: bool = True

class BorrowRequest(BaseModel):
    user_id: int = Field(..., description="The ID of the student or staff borrowing the book")
    book_id: int = Field(..., description="The ID of the book to borrow")

class BorrowRecord(BaseModel):
    record_id: int
    user_id: int
    book_id: int
    borrow_date: date
    due_date: date
    returned: bool = False

class ReturnRequest(BaseModel):
    record_id: int = Field(..., description="The ID of the borrow record to close")

class FineRecord(BaseModel):
    user_id: int
    book_id: int
    days_overdue: int
    fine_amount_usd: float



books_db: List[Book] = [
    Book(book_id=1, title="Clean Code", author="Robert C. Martin", category=Category.technology),
    Book(book_id=2, title="A Brief History of Time", author="Stephen Hawking", category=Category.science),
    Book(book_id=3, title="The Great Gatsby", author="F. Scott Fitzgerald", category=Category.fiction),
    Book(book_id=4, title="Introduction to Algorithms", author="Cormen et al.", category=Category.mathematics),
    Book(book_id=5, title="Sapiens", author="Yuval Noah Harari", category=Category.history),
]

borrow_records_db: List[BorrowRecord] = []
record_counter: int = 1
FINE_PER_DAY: float = 0.50

# end point 1

@app.get("/books", response_model=List[Book], tags=["Books"])
async def search_books(
    title: Optional[str] = Query(None, description="Filter by book title (partial match)"),
    author: Optional[str] = Query(None, description="Filter by author name (partial match)"),
    category: Optional[Category] = Query(None, description="Filter by category"),
) -> List[Book]:
    """
    Search for books by title, author, or category.
    Returns a list of matching books from the library catalogue.
    """
    results: List[Book] = books_db

    if title:
        results = [b for b in results if title.lower() in b.title.lower()]
    if author:
        results = [b for b in results if author.lower() in b.author.lower()]
    if category:
        results = [b for b in results if b.category == category]

    if not results:
        raise HTTPException(status_code=404, detail="No books found matching your search criteria.")

    return results



# ENDPOINT 2 — POST /borrow

@app.post("/borrow", response_model=BorrowRecord, status_code=201, tags=["Borrowing"])
async def borrow_book(request: BorrowRequest) -> BorrowRecord:
    """
    Borrow a book from the library.
    Marks the book as unavailable and creates a borrow record with a 14-day loan period.
    """
    global record_counter

    book: Optional[Book] = next((b for b in books_db if b.book_id == request.book_id), None)

    if book is None:
        raise HTTPException(status_code=404, detail=f"Book with ID {request.book_id} does not exist.")
    if not book.available:
        raise HTTPException(status_code=409, detail="This book is currently on loan. Please check back later.")

    # Mark book as unavailable
    book.available = False

    today: date = date.today()
    record = BorrowRecord(
        record_id=record_counter,
        user_id=request.user_id,
        book_id=request.book_id,
        borrow_date=today,
        due_date=today + timedelta(days=14),
    )
    borrow_records_db.append(record)
    record_counter += 1

    return record

@app.post("/return", tags=["Borrowing"])
async def return_book(request: ReturnRequest) -> dict:
    """
    Return a borrowed book.
    Marks the book as available again and closes the borrow record.
    """
    record: Optional[BorrowRecord] = next(
        (r for r in borrow_records_db if r.record_id == request.record_id), None
    )

    if record is None:
        raise HTTPException(status_code=404, detail=f"Borrow record ID {request.record_id} not found.")
    if record.returned:
        raise HTTPException(status_code=409, detail="This book has already been returned.")

    record.returned = True

    # Mark book available again
    book: Optional[Book] = next((b for b in books_db if b.book_id == record.book_id), None)
    if book:
        book.available = True

    return {"message": "Book returned successfully.", "record_id": record.record_id}


@app.get("/fines/{user_id}", response_model=List[FineRecord], tags=["Fines"])
async def check_fines(user_id: int) -> List[FineRecord]:
    """
    Check overdue books and calculate outstanding fines for a specific user.
    A fine of $0.50 is charged per overdue day.
    """
    today: date = date.today()
    fines: List[FineRecord] = []

    for record in borrow_records_db:
        if record.user_id == user_id and not record.returned and today > record.due_date:
            days_overdue: int = (today - record.due_date).days
            fine_amount: float = round(days_overdue * FINE_PER_DAY, 2)
            fines.append(
                FineRecord(
                    user_id=user_id,
                    book_id=record.book_id,
                    days_overdue=days_overdue,
                    fine_amount_usd=fine_amount,
                )
            )

    return fines


async def simulate_user_borrow(user_id: int, book_id: int) -> None:
    """Simulates a user borrowing a book asynchronously."""
    global record_counter
    await asyncio.sleep(0.1)

    book: Optional[Book] = next((b for b in books_db if b.book_id == book_id), None)
    if book and book.available:
        book.available = False
        today: date = date.today()
        record = BorrowRecord(
            record_id=record_counter,
            user_id=user_id,
            book_id=book_id,
            borrow_date=today,
            due_date=today + timedelta(days=14),
        )
        borrow_records_db.append(record)
        record_counter += 1
        print(f"[User {user_id}] Successfully borrowed '{book.title}' (Record #{record.record_id})")
    else:
        print(f"[User {user_id}] Book ID {book_id} is unavailable or not found.")


async def simulate_user_return(record_id: int) -> None:
    """Simulates a user returning a book asynchronously."""
    await asyncio.sleep(0.05)  # Simulate network delay

    record: Optional[BorrowRecord] = next(
        (r for r in borrow_records_db if r.record_id == record_id), None
    )
    if record and not record.returned:
        record.returned = True
        book: Optional[Book] = next((b for b in books_db if b.book_id == record.book_id), None)
        if book:
            book.available = True
        print(f"[Record {record_id}] Book returned successfully.")
    else:
        print(f"[Record {record_id}] Return failed — record not found or already returned.")


async def run_concurrent_simulation() -> None:
    """
    Demonstrates multiple users borrowing and returning books concurrently
    using asyncio.gather() to run tasks simultaneously.
    """
    print("\n" + "=" * 55)
    print("   CONCURRENT USER SIMULATION")
    print("=" * 55)
    print("Simulating 4 users accessing the library at the same time...\n")

    # Four users attempt to borrow books at the same time
    await asyncio.gather(
        simulate_user_borrow(user_id=101, book_id=1),
        simulate_user_borrow(user_id=102, book_id=2),
        simulate_user_borrow(user_id=103, book_id=1),  # Same book — should be denied
        simulate_user_borrow(user_id=104, book_id=3),
    )

    print("\nNow simulating two users returning books concurrently...\n")

    # Two users return books at the same time
    await asyncio.gather(
        simulate_user_return(record_id=1),
        simulate_user_return(record_id=2),
    )

    print("\n" + "=" * 55)
    print("   SIMULATION COMPLETE")
    print("=" * 55)



if __name__ == "__main__":
    print("\nLimkokwing Library API — Async Simulation Mode")
    print("(Run with `uvicorn library_api:app --reload` for the full API server)\n")

    asyncio.run(run_concurrent_simulation())

    print("\nFinal Book Availability Status:")
    for book in books_db:
        status = "Available" if book.available else "On Loan"
        print(f"  [{book.book_id}] {book.title} — {status}")

    print("\nAll Borrow Records:")
    for rec in borrow_records_db:
        status = "Returned" if rec.returned else "Active"
        print(f"  Record #{rec.record_id} | User {rec.user_id} | Book {rec.book_id} | Due: {rec.due_date} | {status}")