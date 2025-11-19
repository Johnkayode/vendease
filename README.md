# Vendease

[![CI Status](https://github.com/Johnkayode/vendease/actions/workflows/test.yml/badge.svg)](https://github.com/Johnkayode/vendease/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> [!NOTE]
> This project is a submission.

- **Framework**: Python/Django
- **Database**: PostgreSQL

## Setup and Installation

1. Ensure Docker is installed on your machine.
2. Clone the repository:
    ```bash
    git clone https://github.com/johnkayode/vendease.git
    ```
3. Configure environment:
   ```bash
   cp .env.example .env
   ```
4. Build and run the services:
    ```bash
    make up
    ```
5. The API will be running on `http://localhost:8000` 

## API Documentation
Postman: [here](http://localhost:8000/api/)

## Testing
Test environment is set up with Github Actions.
Run locally:

```bash
make test
```