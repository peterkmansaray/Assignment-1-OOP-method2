# Assignment-1-OOP-method2
​Limkokwing Library Digital System API
​Project Description
​This project is a basic digital library system designed for Limkokwing University. It provides a secure and efficient API for library staff to manage book inventories, handle student borrowings, process returns, and track overdue fines.  
​The system is built using Python FastAPI and utilizes Asynchronous Programming to support multiple users accessing the library services simultaneously. It features full Type Annotations to ensure code reliability and a user-friendly interface for staff with limited technical knowledge.  
​Key Features
​Book Search: Filter the library catalogue by title, author, or category.  
​Borrowing System: Asynchronous processing of book loans with a 14-day due date.  
​Return Management: Automated system to mark books as available upon return.  
​Fine Tracking: Automatic calculation of overdue fines at a rate of $0.50 per day.  
​Concurrent Access: Support for multiple simultaneous requests using asyncio.  
​Tech Stack
​Language: Python 3.x
​Framework: FastAPI
​Server: Uvicorn (ASGI)
​Data Handling: Pydantic for data validation and type safety
