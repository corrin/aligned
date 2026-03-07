# FastREST Reference

**DRF-inspired async REST framework for FastAPI** (v0.1.2, Beta)
- Repo: https://github.com/hoaxnerd/fastrest
- Example app: https://github.com/hoaxnerd/fastrest-example

## Installation

```bash
pip install fastrest[sqlalchemy,mcp]  # Full install
pip install fastrest[sqlalchemy]      # Most common
pip install fastrest                  # Core only (BYO ORM adapter)
```

**Requirements:** Python 3.10+, FastAPI 0.100+, Pydantic 2.0+, SQLAlchemy 2.0+ (async)

---

## Quick Start

```python
# 1. Model
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    bio = Column(String(1000))
    is_active = Column(Boolean, default=True)

# 2. Serializer
from fastrest.serializers import ModelSerializer

class AuthorSerializer(ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio", "is_active"]
        read_only_fields = ["id"]

# 3. ViewSet
from fastrest.viewsets import ModelViewSet

class AuthorViewSet(ModelViewSet):
    queryset = Author
    serializer_class = AuthorSerializer

# 4. Router + App
from fastapi import FastAPI
from fastrest.routers import DefaultRouter

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="author")

app = FastAPI(title="My API")
app.include_router(router.urls, prefix="/api")
```

**Auto-generated endpoints:**
- `GET /api/authors` - List
- `POST /api/authors` - Create (201)
- `GET /api/authors/{pk}` - Retrieve
- `PUT /api/authors/{pk}` - Update
- `PATCH /api/authors/{pk}` - Partial update
- `DELETE /api/authors/{pk}` - Delete (204)
- `GET /api/` - API root
- `GET /docs` - Swagger UI
- `GET /SKILL.md` - Agent docs
- `GET /manifest.json` - API metadata

---

## Package Structure

```
src/fastrest/
  __init__.py           # Public API exports
  serializers.py        # BaseSerializer, Serializer, ModelSerializer, ListSerializer
  fields.py             # 25+ field types
  views.py              # APIView (base dispatch, auth, permissions, throttling)
  viewsets.py           # ViewSetMixin, ModelViewSet, ReadOnlyModelViewSet
  generics.py           # Generic views (ListCreateAPIView, etc.)
  mixins.py             # CreateModelMixin, ListModelMixin, etc.
  routers.py            # SimpleRouter, DefaultRouter
  decorators.py         # @action, @api_view
  request.py            # Request wrapper (adds .data, .user, .auth)
  response.py           # Response (extends JSONResponse with .data)
  exceptions.py         # APIException hierarchy, ValidationError
  permissions.py        # IsAuthenticated, HasScope, composable with & | ~
  authentication.py     # TokenAuth, BasicAuth, SessionAuth
  throttling.py         # SimpleRateThrottle, AnonRateThrottle, UserRateThrottle
  pagination.py         # PageNumberPagination, LimitOffsetPagination
  filters.py            # SearchFilter, OrderingFilter
  settings.py           # configure(), get_settings()
  status.py             # HTTP status constants
  openapi.py            # Pydantic model generation from serializers
  skills.py             # SKILL.md generation for AI agents
  mcp.py                # MCP server integration
  manifest.py           # API manifest generation
  negotiation.py        # Content negotiation, renderers
  test.py               # APIClient (async test utilities)
  relations.py          # Relation field handling
  compat/orm/
    base.py             # ORMAdapter interface
    sqlalchemy.py       # SQLAlchemy async adapter
```

---

## Key Concepts

### Serializers

ModelSerializer auto-generates fields from SQLAlchemy model columns. Validation runs at three levels:

```python
class BookSerializer(ModelSerializer):
    price = FloatField(min_value=0.01)  # Override auto-generated field

    class Meta:
        model = Book
        fields = ["id", "title", "isbn", "price", "author_id"]
        read_only_fields = ["id"]

    # Level 1: Field-level validation
    def validate_isbn(self, value):
        if value and len(value) not in (10, 13):
            raise ValidationError("ISBN must be 10 or 13 characters.")
        return value

    # Level 2: Object-level validation
    def validate(self, attrs):
        if attrs.get("rating", 0) < 3 and not attrs.get("comment"):
            raise ValidationError("Low ratings require a comment.")
        return attrs

    # Level 3: Field constraints (min_value, max_length, etc.)
```

**Field types:** CharField, IntegerField, FloatField, BooleanField, DecimalField, DateTimeField, DateField, TimeField, UUIDField, EmailField, URLField, SlugField, ListField, DictField, JSONField, SerializerMethodField, ReadOnlyField, HiddenField, FileField, ImageField, IPAddressField, ChoiceField, MultipleChoiceField, RegexField, DurationField

### ViewSets

```python
class BookViewSet(ModelViewSet):
    queryset = Book
    serializer_class = BookSerializer

    # Action-specific serializer
    def get_serializer_class(self):
        if self.action == "retrieve":
            return BookDetailSerializer
        return BookSerializer
```

### Custom Actions

```python
from fastrest.decorators import action
from fastrest.response import Response

class BookViewSet(ModelViewSet):
    queryset = Book
    serializer_class = BookSerializer

    @action(methods=["get"], detail=False, url_path="in-stock")
    async def in_stock(self, request, **kwargs):
        books = await self.adapter.filter_queryset(
            Book, self.get_session(), in_stock=True
        )
        serializer = self.get_serializer(books, many=True)
        return Response(data=serializer.data)

    @action(methods=["post"], detail=True, url_path="toggle-stock")
    async def toggle_stock(self, request, **kwargs):
        book = await self.get_object()
        session = self.get_session()
        await self.adapter.update(book, session, in_stock=not book.in_stock)
        serializer = self.get_serializer(book)
        return Response(data=serializer.data)
```

### Pagination

```python
from fastrest.pagination import PageNumberPagination, LimitOffsetPagination

class BookPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100

class BookViewSet(ModelViewSet):
    queryset = Book
    serializer_class = BookSerializer
    pagination_class = BookPagination
```

Response envelope: `{count, next, previous, results}`

### Filtering & Search

```python
from fastrest.filters import SearchFilter, OrderingFilter

class BookViewSet(ModelViewSet):
    queryset = Book
    serializer_class = BookSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description", "isbn"]
    ordering_fields = ["title", "price"]
    ordering = ["title"]  # default
```

- `?search=django` - case-insensitive search across search_fields
- `?ordering=-price,title` - multi-field sort

### Permissions

Composable with `&`, `|`, `~`:

```python
from fastrest.permissions import BasePermission, IsAuthenticated, HasScope

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id

class ArticleViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated & IsOwner]
    # Or scope-based:
    # permission_classes = [IsAuthenticated & HasScope("articles:read")]
```

Built-in: AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, HasScope

### Authentication

```python
from fastrest.authentication import TokenAuthentication, BasicAuthentication, SessionAuthentication

token_auth = TokenAuthentication(get_user_by_token=my_lookup_fn)
# Authorization: Token <key>  (or Bearer with keyword="Bearer")

basic_auth = BasicAuthentication(get_user_by_credentials=my_creds_fn)
# Authorization: Basic <base64>

session_auth = SessionAuthentication(get_user_from_session=my_session_fn)
```

Unauthenticated requests return 401 (not 403).

### Throttling

```python
from fastrest.throttling import SimpleRateThrottle, AnonRateThrottle, UserRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    rate = "60/min"
    def get_cache_key(self, request, view):
        return f"burst_{self.get_ident(request)}"
```

Rate strings: `"5/sec"`, `"10/min"`, `"100/hour"`, `"1000/day"`. Returns 429 with Retry-After header.

### App Configuration

```python
from fastrest.settings import configure

configure(app, {
    "DEFAULT_PAGINATION_CLASS": "fastrest.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_PERMISSION_CLASSES": ["fastrest.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [token_auth],
    "SKILL_NAME": "my-api",
    "MCP_PREFIX": "/mcp",
})
```

Resolution order: viewset attribute > app config > framework default. Unknown keys raise ValueError (unless STRICT_SETTINGS=False).

### Routers

```python
from fastrest.routers import DefaultRouter, SimpleRouter

router = DefaultRouter()  # Includes API root, SKILL.md, manifest.json
router.register("authors", AuthorViewSet, basename="author")
router.register("books", BookViewSet, basename="book")

# SimpleRouter: no root view
```

Per-method OpenAPI routes with correct status codes, typed pk params, auto-generated Pydantic schemas, tag grouping, unique operation IDs.

### Generic Views

For when you don't need a full viewset:

```python
from fastrest.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

class AuthorList(ListCreateAPIView):
    queryset = Author
    serializer_class = AuthorSerializer

class AuthorDetail(RetrieveUpdateDestroyAPIView):
    queryset = Author
    serializer_class = AuthorSerializer
```

Available: CreateAPIView, ListAPIView, RetrieveAPIView, DestroyAPIView, UpdateAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveDestroyAPIView, RetrieveUpdateDestroyAPIView

### Agent Integration

**SKILL.md** - Auto-generated AI agent docs:

```python
class BookViewSet(ModelViewSet):
    skill_description = "Manage the book catalog"
    skill_exclude_actions = ["destroy"]
    skill_examples = [{"description": "Search books", "request": "GET /books?search=python", "response": "200"}]
```

**MCP Server** - Model Context Protocol tools from viewsets:

```python
from fastrest.mcp import mount_mcp
mount_mcp(app, router)
# Auto-generates tools: books_list, books_create, books_retrieve, etc.
```

**Manifest** - `GET /manifest.json` structured metadata.

### Testing

```python
from fastrest.test import APIClient

@pytest.fixture
def client(app):
    return APIClient(app)

@pytest.mark.asyncio
async def test_create_author(client):
    resp = await client.post("/api/authors", json={"name": "Author"})
    assert resp.status_code == 201
```

Methods: get(), post(), put(), patch(), delete(), force_authenticate(), credentials(), logout()

---

## Exceptions

| Exception | Status |
|-----------|--------|
| APIException | 500 |
| ValidationError | 400 |
| ParseError | 400 |
| AuthenticationFailed | 401 |
| NotAuthenticated | 401 |
| PermissionDenied | 403 |
| NotFound | 404 |
| MethodNotAllowed | 405 |
| UnsupportedMediaType | 415 |
| Throttled | 429 |

---

## Architecture Notes

- **Async throughout**: All handlers, mixins, serializers, ORM adapter are async
- **Per-method routes**: Unlike DRF, each HTTP method gets its own FastAPI route with unique operation ID and Pydantic schema
- **ORM adapter pattern**: `compat/orm/base.py` defines the ORMAdapter interface; SQLAlchemy is the provided implementation, but the design supports other ORMs
- **Settings cascade**: viewset attribute > app config (via configure()) > framework default
