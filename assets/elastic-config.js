// Public read config for GitHub Pages. Read-only API key scoped to solis-watch.
// Run: python3 scripts/write_pages_config.py after setting ELASTICSEARCH_READ_API_KEY in .env
window.SOLIS_ELASTIC = {
  endpoint: "https://ai-assistants-ffcafb.es.us-east-1.aws.elastic.cloud",
  index: "solis-watch",
  reportId: "report-current",
  apiKey: ""
};
