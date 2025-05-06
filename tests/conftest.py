import sys
import vcr
from pathlib import Path

# Ensure src/ is on sys.path for all tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Configure VCR for recording API responses
vcr_config = {
    # Don't record sensitive headers like API keys
    'filter_headers': ['authorization', 'Authorization', 'x-goog-api-key'],
    # Record once and reuse for subsequent test runs
    'record_mode': 'once',
    # Where to store cassettes
    'cassette_library_dir': 'tests/fixtures/vcr_cassettes',
    # Match on method, URL, and body
    'match_on': ['method', 'scheme', 'host', 'port', 'path', 'query'],
    # Automatically filter out API keys from query parameters
    'filter_query_parameters': ['key', 'api_key'],
}
