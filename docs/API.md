# ResAI API Reference

Version: `v1`  
Base URL: `/api/v1`

## Endpoints Summary

### Research Runs
- `POST /api/v1/research`: Create new research run & generate plan.
- `GET /api/v1/research`: List recent research runs.
- `GET /api/v1/research/{research_id}`: Get research run status.
- `POST /api/v1/research/{research_id}/cancel`: Cancel active run.
- `POST /api/v1/research/{research_id}/rerun`: Rerun research question for freshness check.
- `GET /api/v1/research/{research_id}/events`: SSE endpoint for live workflow streaming.

### Plans & Review
- `GET /api/v1/research/{research_id}/plan`: Get latest generated research plan.
- `POST /api/v1/research/{research_id}/plan/regenerate`: Regenerate plan using user feedback.
- `PATCH /api/v1/research/{research_id}/plan`: Edit plan subquestions or main question.
- `POST /api/v1/research/{research_id}/plan/approve`: Approve plan & trigger execution.

### Evidence & Sources
- `GET /api/v1/research/{research_id}/sources`: List retrieved sources.
- `GET /api/v1/research/{research_id}/evidence`: List claim-level evidence records.
- `GET /api/v1/research/{research_id}/coverage`: Dynamic Research Coverage Map metrics.
- `GET /api/v1/research/{research_id}/contradictions`: List identified cross-source contradictions.
- `GET /api/v1/research/{research_id}/tool-calls`: Tool call execution audit logs.

### Reports & Exports
- `GET /api/v1/research/{research_id}/report`: Get generated report.
- `POST /api/v1/reports/{report_id}/validate-citations`: Run citation validation pass.
- `POST /api/v1/reports/{report_id}/summarize`: Generate executive/findings summary.
- `GET /api/v1/reports/{report_id}/export?format=pdf|docx|md|json|csv`: Download report files.

### Uploads & Tools
- `POST /api/v1/uploads`: Upload PDF, CSV, XLSX, TXT, or Markdown documents.
- `GET /api/v1/tools`: List registered tools.
- `POST /api/v1/tools`: Register custom tool schema.
- `GET /api/v1/health`: System health status.
