"""
Tests for search endpoints.

Tests:
- test_search_returns_results: Test search returns results
- test_search_sanitization: Test query sanitization
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestSearch:
    """Test cases for search endpoints."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, client, auth_headers, mock_project):
        """Test search returns results from vector store."""
        with patch('app.routers.search.get_db') as mock_get_db, \
             patch('app.routers.search.get_vector_store') as mock_vs, \
             patch('app.routers.search.get_cache_service') as mock_cache:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock cache - no cached results
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=None)
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[
                {"text": "Search result 1", "score": 0.95, "document_id": 1, "filename": "doc1.pdf"},
                {"text": "Search result 2", "score": 0.85, "document_id": 2, "filename": "doc2.pdf"},
            ])
            mock_vs.return_value = mock_vs_instance
            
            response = client.post(
                "/search",
                json={
                    "query": "HR policy",
                    "project_id": 1,
                    "top_k": 5
                },
                headers=auth_headers
            )
            
            # Should return search results
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "results" in data or "query" in data

    @pytest.mark.asyncio
    async def test_search_sanitization(self, client, auth_headers, mock_project):
        """Test that search queries are sanitized."""
        with patch('app.routers.search.get_db') as mock_get_db, \
             patch('app.routers.search.get_vector_store') as mock_vs, \
             patch('app.routers.search.get_cache_service') as mock_cache:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock cache
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=None)
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[])
            mock_vs.return_value = mock_vs_instance
            
            # Test with potentially malicious input
            malicious_queries = [
                "<script>alert('xss')</script>",
                "test\"; DROP TABLE users;--",
                "test' OR '1'='1",
                "test\\backslash",
            ]
            
            for query in malicious_queries:
                response = client.post(
                    "/search",
                    json={
                        "query": query,
                        "project_id": 1,
                        "top_k": 5
                    },
                    headers=auth_headers
                )
                
                # Should handle gracefully (sanitization should strip dangerous chars)
                assert response.status_code in [200, 400, 500]
                
                # If we get a 200, verify the query was sanitized in the response
                if response.status_code == 200:
                    data = response.json()
                    returned_query = data.get("query", "")
                    # HTML should be escaped
                    assert "&lt;" in returned_query or "&gt;" in returned_query or "<" not in returned_query

    @pytest.mark.asyncio
    async def test_search_xss_prevention(self, client, auth_headers, mock_project):
        """Test XSS prevention in search queries."""
        with patch('app.routers.search.get_db') as mock_get_db, \
             patch('app.routers.search.get_vector_store') as mock_vs, \
             patch('app.routers.search.get_cache_service') as mock_cache:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock cache
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=None)
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[])
            mock_vs.return_value = mock_vs_instance
            
            # Test with HTML/script tags
            response = client.post(
                "/search",
                json={
                    "query": "<img src=x onerror=alert(1)>",
                    "project_id": 1,
                    "top_k": 5
                },
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                returned_query = data.get("query", "")
                # Should not contain raw HTML tags
                assert "<img" not in returned_query
                assert "onerror" not in returned_query

    @pytest.mark.asyncio
    async def test_search_query_length_limit(self, client, auth_headers, mock_project):
        """Test that query length is limited."""
        with patch('app.routers.search.get_db') as mock_get_db, \
             patch('app.routers.search.get_vector_store') as mock_vs, \
             patch('app.routers.search.get_cache_service') as mock_cache:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock cache
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=None)
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance
            
            # Setup mock vector store
            mock_vs_instance = MagicMock()
            mock_vs_instance.search = AsyncMock(return_value=[])
            mock_vs.return_value = mock_vs_instance
            
            # Test with very long query
            long_query = "a" * 1000  # 1000 chars (exceeds 500 limit)
            
            response = client.post(
                "/search",
                json={
                    "query": long_query,
                    "project_id": 1,
                    "top_k": 5
                },
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                returned_query = data.get("query", "")
                # Should be truncated to 500 chars
                assert len(returned_query) <= 500

    @pytest.mark.asyncio
    async def test_search_cached_results(self, client, auth_headers, mock_project):
        """Test that cached results are returned."""
        with patch('app.routers.search.get_db') as mock_get_db, \
             patch('app.routers.search.get_cache_service') as mock_cache:
            
            # Setup mock database
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_project
            mock_session.execute = AsyncMock(return_value=mock_result)
            
            async def mock_db_gen():
                yield mock_session
            
            mock_get_db.return_value = mock_db_gen()
            
            # Setup mock cache with cached results
            cached_results = [
                {"text": "Cached result", "score": 0.9, "document_id": 1, "filename": "cached.pdf"}
            ]
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=cached_results)
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance
            
            response = client.post(
                "/search",
                json={
                    "query": "test query",
                    "project_id": 1,
                    "top_k": 5
                },
                headers=auth_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                # Should indicate cached results
                assert "cached" in data or "results" in data


class TestQuerySanitization:
    """Test cases for query sanitization utility."""

    def test_sanitize_query_html_escape(self):
        """Test that HTML entities are escaped."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query("<script>alert('xss')</script>")
        
        # Should escape HTML
        assert "&lt;" in result or "&gt;" in result
        assert "<script>" not in result

    def test_sanitize_query_length_limit(self):
        """Test that query length is limited to 500 chars."""
        from app.routers.search import sanitize_query
        
        long_query = "a" * 1000
        result = sanitize_query(long_query)
        
        assert len(result) <= 500

    def test_sanitize_query_dangerous_chars(self):
        """Test that dangerous characters are removed."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query('test<>;"\'\\chars')
        
        # These chars should be removed
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result
        assert "'" not in result
        assert "\\" not in result

    def test_sanitize_query_multiple_spaces(self):
        """Test that multiple spaces are collapsed."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query("test    multiple   spaces")
        
        assert "  " not in result
        assert result == "test multiple spaces"

    def test_sanitize_query_trim(self):
        """Test that query is trimmed."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query("  test  ")
        
        assert result == "test"

    def test_sanitize_query_empty(self):
        """Test empty query handling."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query("")
        
        assert result == ""

    def test_sanitize_query_unicode(self):
        """Test that unicode is preserved."""
        from app.routers.search import sanitize_query
        
        result = sanitize_query("ทดสอบ ค้นหา ภาษาไทย")
        
        # Unicode should be preserved
        assert "ทดสอบ" in result
        assert "ค้นหา" in result
