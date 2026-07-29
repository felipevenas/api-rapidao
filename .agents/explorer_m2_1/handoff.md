# Handoff Report — Marco 2: Store & Menu Management Modeling

**De:** `explorer_m2_1` (teamwork_preview_explorer)  
**Para:** `orchestrator` / `implementer_m2_1`  
**Data/Hora:** 2026-07-28T21:56:30Z  

---

## 1. Observation

Direct observations from the codebase investigation:
- **Base ORM and Database Engine**: `app/core/database.py` lines 26-28 defines `class Base(DeclarativeBase): pass` and async engine configuration for PostgreSQL `create_async_engine(settings.SQLALCHEMY_DATABASE_URI)`.
- **User ORM Model**: `app/domain/auth/models.py` lines 15-35 defines `User` table `"users"` with `id` of type `UUID(as_uuid=True)` and role enum (`UserRole.STORE`).
- **Auth Schemas**: `app/domain/auth/schemas.py` lines 51-54 defines envelope generic model `APIResponse[T]` with fields `status`, `message`, `data`.
- **Clean Architecture & Cross-Domain Constraints**: `INSTRUCTIONS.md` (lines 35-49) specifies layer order `Routes -> Service -> Repository -> Model` and prohibits direct imports of `model.py`, `service.py`, or `repository.py` from other domain folders without a `usecase.py`.
- **Requirements for Store & Product**: `PROJECT.md` (lines 38-43) and `ORIGINAL_REQUEST.md` (lines 28-30) require CRUD operations for stores, products, availability toggling, and Redis caching (`store:{id}:menu`).

---

## 2. Logic Chain

1. **Isolation of Domains**: `domain/store/models.py` must reference the user table for the store owner. Observation 4 mandates avoiding cross-domain python imports. Therefore, using string `ForeignKey("users.id", ondelete="CASCADE")` on `Store.owner_id` establishes database integrity without importing `User` from `domain/auth/models.py`.
2. **Support for Haversine Distance Calculation (M3)**: `Store` model must include `lat` and `lng` columns as `Float` in SQLAlchemy and validated floats (`ge=-90.0, le=90.0` / `ge=-180.0, le=180.0`) in Pydantic schemas to ensure valid coordinates for freight calculation.
3. **Product Financial Precision**: `Product.price` uses `Numeric(10, 2, asdecimal=False)` in SQLAlchemy and `float = Field(..., gt=0)` in Pydantic v2 to enforce monetary precision and positive values while preserving straightforward JSON serialization.
4. **Redis Cache Payload Alignment**: `MenuResponse` schema combines store metadata and active product listings into a single model, enabling direct JSON serialization/deserialization for Redis key `store:{id}:menu`.
5. **Pydantic v2 Compatibility**: All response models (`StoreResponse`, `ProductResponse`, `MenuResponse`) include `model_config = ConfigDict(from_attributes=True)` as established in Observation 3.

---

## 3. Caveats

- **No source code written in `app/`**: This investigation is strictly read-only. Proposed code structures are documented in `analysis.md` and this handoff.
- **Database Migrations**: Alembic migrations have not yet been executed in M1. When implementing M2, tables will be automatically created via SQLAlchemy metadata or an Alembic migration script.

---

## 4. Conclusion

The data models `Store` and `Product` in `app/domain/store/models.py` and Pydantic v2 schemas (`StoreCreate`, `StoreUpdate`, `StoreResponse`, `ProductCreate`, `ProductUpdate`, `ProductResponse`, `MenuResponse`) in `app/domain/store/schemas.py` are fully designed, documented, and compliant with Clean Architecture, DDD, and project constraints.

---

## 5. Verification Method

To verify the design and implementation when created by `implementer_m2_1`:

1. **File Inspection**:
   - Verify `app/domain/store/models.py` matches the ORM structure defined in `analysis.md`.
   - Verify `app/domain/store/schemas.py` matches the Pydantic v2 schema definitions in `analysis.md`.
2. **Static & Lint Check**:
   - Run `pytest` or Python syntax verification in `app/`:
     ```powershell
     python -c "from domain.store.models import Store, Product; from domain.store.schemas import StoreCreate, MenuResponse"
     ```
3. **Invalidation Condition**:
   - Any direct import of `domain.auth.models` inside `domain/store/models.py` violates Rule 2 of `INSTRUCTIONS.md`.
