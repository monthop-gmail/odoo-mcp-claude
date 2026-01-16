"""Odoo XML-RPC Client for connecting to Odoo ERP."""

import xmlrpc.client
from typing import Any


class OdooClient:
    """Client for interacting with Odoo via XML-RPC API."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """Initialize Odoo client.

        Args:
            url: Odoo server URL (e.g., https://myodoo.com)
            db: Database name
            username: Odoo username (email)
            password: Odoo password or API key
        """
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self._uid: int | None = None
        self._common: xmlrpc.client.ServerProxy | None = None
        self._models: xmlrpc.client.ServerProxy | None = None

    @property
    def common(self) -> xmlrpc.client.ServerProxy:
        """Get common endpoint proxy."""
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/common",
                allow_none=True,
            )
        return self._common

    @property
    def models(self) -> xmlrpc.client.ServerProxy:
        """Get models endpoint proxy."""
        if self._models is None:
            self._models = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/object",
                allow_none=True,
            )
        return self._models

    def authenticate(self) -> int:
        """Authenticate with Odoo and return user ID.

        Returns:
            User ID if authentication successful

        Raises:
            Exception: If authentication fails
        """
        uid = self.common.authenticate(self.db, self.username, self.password, {})
        if not uid:
            raise Exception(
                f"Authentication failed for user '{self.username}' on database '{self.db}'"
            )
        self._uid = uid
        return uid

    @property
    def uid(self) -> int:
        """Get authenticated user ID, authenticating if necessary."""
        if self._uid is None:
            self.authenticate()
        return self._uid  # type: ignore

    def execute(
        self,
        model: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a method on an Odoo model.

        Args:
            model: Model name (e.g., 'res.partner')
            method: Method name (e.g., 'search_read')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result from Odoo
        """
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            method,
            list(args),
            kwargs,
        )

    def search(
        self,
        model: str,
        domain: list | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[int]:
        """Search for record IDs matching the domain.

        Args:
            model: Model name
            domain: Search domain (list of conditions)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Sort order (e.g., 'name asc, id desc')

        Returns:
            List of matching record IDs
        """
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order
        return self.execute(model, "search", domain, **kwargs)

    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str] | None = None,
    ) -> list[dict]:
        """Read records by IDs.

        Args:
            model: Model name
            ids: List of record IDs to read
            fields: List of fields to read (None for all fields)

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields is not None:
            kwargs["fields"] = fields
        return self.execute(model, "read", ids, **kwargs)

    def search_read(
        self,
        model: str,
        domain: list | None = None,
        fields: list[str] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict]:
        """Search and read records in one call.

        Args:
            model: Model name
            domain: Search domain
            fields: Fields to read
            offset: Number of records to skip
            limit: Maximum number of records
            order: Sort order

        Returns:
            List of matching records with specified fields
        """
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if fields is not None:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order
        return self.execute(model, "search_read", domain, **kwargs)

    def search_count(
        self,
        model: str,
        domain: list | None = None,
    ) -> int:
        """Count records matching the domain.

        Args:
            model: Model name
            domain: Search domain

        Returns:
            Number of matching records
        """
        domain = domain or []
        return self.execute(model, "search_count", domain)

    def create(
        self,
        model: str,
        values: dict,
    ) -> int:
        """Create a new record.

        Args:
            model: Model name
            values: Field values for the new record

        Returns:
            ID of the created record
        """
        return self.execute(model, "create", values)

    def write(
        self,
        model: str,
        ids: list[int],
        values: dict,
    ) -> bool:
        """Update existing records.

        Args:
            model: Model name
            ids: Record IDs to update
            values: Field values to update

        Returns:
            True if successful
        """
        return self.execute(model, "write", ids, values)

    def unlink(
        self,
        model: str,
        ids: list[int],
    ) -> bool:
        """Delete records.

        Args:
            model: Model name
            ids: Record IDs to delete

        Returns:
            True if successful
        """
        return self.execute(model, "unlink", ids)

    def fields_get(
        self,
        model: str,
        attributes: list[str] | None = None,
    ) -> dict:
        """Get field definitions for a model.

        Args:
            model: Model name
            attributes: Field attributes to return (e.g., ['string', 'type'])

        Returns:
            Dictionary of field definitions
        """
        kwargs = {}
        if attributes is not None:
            kwargs["attributes"] = attributes
        return self.execute(model, "fields_get", **kwargs)

    def check_access_rights(
        self,
        model: str,
        operation: str,
        raise_exception: bool = False,
    ) -> bool:
        """Check if user has access rights for an operation.

        Args:
            model: Model name
            operation: Operation to check ('read', 'write', 'create', 'unlink')
            raise_exception: Whether to raise exception on access denied

        Returns:
            True if access is allowed
        """
        return self.execute(
            model,
            "check_access_rights",
            operation,
            raise_exception=raise_exception,
        )

    def get_version(self) -> dict:
        """Get Odoo server version info.

        Returns:
            Version information dictionary
        """
        return self.common.version()
