# ADR 0006: LLM-Assisted Agenda Parsing with Claude on Amazon Bedrock

## Status
Accepted

## Context
Spry users schedule meetings and organize team agendas. Agendas often arrive as unstructured free text (emails, Slack threads, notes, chat transcripts). Manually transcribing topics, owners, durations, and action items into form fields is tedious and error-prone.

Key architectural and operating constraints:
1. **Network & VPC Isolation**: The core Spry API runs inside private subnets with no NAT gateway to minimize infrastructure costs. The database (Aurora Serverless v2) has no public access.
2. **Cost Sensitivity**: Running dedicated background infrastructure or NAT gateways ($33/month + data transfer) for intermittent AI calls is economically unjustified for small-to-medium workloads.
3. **External Untrusted Input**: Pasted text is external data and must be treated as untrusted input. It may contain accidental commands or deliberate prompt injection attacks.
4. **Data Integrity & Human-in-the-Loop**: The model must never write directly to the database. The design must adhere to "the model suggests, the person decides."

## Decision
1. **Model Selection**: We use Claude on Amazon Bedrock (`anthropic.claude-opus-5-5` by default, configurable via `PARSER_MODEL`). Claude Opus provides exceptional multilingual reasoning (handling Ukrainian, English, relative dates, and implicit action items) and reliable adherence to tool calling without emitting hallucinations or invented values. Model IDs are decoupled from code and defined in configuration.
2. **Parser Runs Outside the VPC**: The agenda parser Lambda runs outside the VPC and connects to Amazon Bedrock Mantle over the public internet. This avoids provisioning an expensive NAT gateway or dedicated VPC interface endpoint.
3. **No Direct Database Access**: The parser Lambda has no database credentials or VPC access (`VpcConfig: null`). It functions strictly as a pure transformer: receiving raw text and returning structured JSON.
4. **Human Review Before Save**: The parser returns JSON to the browser. The frontend populates the agenda form with visual "suggested" badges on model-filled fields. The user reviews, edits, and explicitly clicks "Save".
5. **Persistence via Main API**: The save action posts through the existing backend API endpoint (`POST /api/agendas`). The main API validates the data according to business rules and persists both the final edited agenda and the original suggestion (`ai_suggestion JSONB`, `model`, `prompt_version`) for auditability and quality evaluation.
6. **Delimited Data & Tool Calling**: Pasted text is strictly enclosed in `<pasted_text>` XML tags. The system prompt instructs Claude that the text is data, not instructions, and requires calling the single tool `record_agenda` with the Pydantic-defined JSON schema.
7. **IAM Permissions**: The Lambda IAM role is granted `bedrock-mantle:CreateInference` on `Resource: "*"`. Narrowing the resource ARN to specific models is noted as an immediate operational follow-up once AWS Bedrock Mantle resource-level ARNs are fully stabilized.

## Alternatives Considered

1. **Calling Bedrock from the Main API via a VPC Interface Endpoint**:
   - *Why it lost*: An AWS PrivateLink VPC interface endpoint for Bedrock incurs an hourly base charge (~$7.30/month per AZ, ~$22/month across 3 AZs) regardless of whether any requests are processed. Running the parser as a serverless Lambda outside the VPC costs $0 when idle.
2. **Direct Anthropic Claude API (Direct SaaS) instead of Amazon Bedrock**:
   - *Why it lost*: Calling the public Anthropic API requires managing external third-party API keys, separate billing, and handling credentials in secrets managers. Amazon Bedrock uses native AWS IAM authentication, integrates with AWS CloudTrail, obeys AWS account policies, and allows consolidated billing with AWS Budgets.
3. **Regular Expression or Rule-Based Heuristic Parser**:
   - *Why it lost*: Rule-based parsing fails on varied natural language formats, multi-language input (e.g. Ukrainian vs English), conversational chat snippets, relative date expressions ("by end of week", "next Tuesday after lunch"), and implicit task ownership.

## Consequences

- **Cost**: Inference costs scale linearly with usage (~$4.00 per 1M input tokens, ~$20.00 per 1M output tokens for Opus; ~$0.10/$0.50 for Haiku). For a typical agenda parse (≈ 1,200 input tokens, 250 output tokens), cost is ≈ $0.0098 per parse.
- **Monitoring & Auditing**: Every parse outputs exactly one structured JSON log line containing: `event: agenda_parsed`, `user`, `model`, `prompt_version`, `input_tokens`, `output_tokens`, `latency_ms`, and `cost_usd`.
- **Fault Tolerance**: If Amazon Bedrock experiences an outage or throttling, the parser returns a descriptive 429/500 error. The user can continue typing and saving agendas manually in the UI without interruption. Spry's core scheduling features remain completely decoupled and available.
- **Safety**: Prompt injection attacks cannot execute database commands or exfiltrate data because the parser is stateless, read-only, has no database connection, and output is strictly mediated through user review.
