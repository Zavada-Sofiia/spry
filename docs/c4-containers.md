# C4 Container Diagram (Level 2) — Spry Architecture

```mermaid
graph TD
    User["User (Browser)"]

    subgraph AWS ["Amazon Web Services"]
        subgraph PublicCloud ["Public Internet / Outside VPC"]
            CloudFront["CloudFront Distribution & S3<br/>(React Single Page App)"]
            Cognito["Amazon Cognito User Pool<br/>(Authentication & JWT)"]
            ParserLambda["Lambda: Agenda Parser<br/>(No VPC, Python 3.12 / Anthropic SDK)"]
            Bedrock["Amazon Bedrock<br/>(Claude Opus 5.5 via Mantle)"]
        end

        subgraph VPC ["Spry VPC (Private Subnets)"]
            BackendAPI["FastAPI Backend Service<br/>(ECS Fargate / Uvicorn)"]
            AuroraDB[("Amazon Aurora Serverless v2<br/>(PostgreSQL)")]
        end
    end

    User -->|"1. Load Web App"| CloudFront
    User -->|"2. Authenticate"| Cognito
    
    %% Parse flow
    User -.->|"3. [PARSE] POST raw text + JWT"| ParserLambda
    ParserLambda -->|"Invoke Mantle Messages API"| Bedrock
    Bedrock -.->|"Return structured JSON"| ParserLambda
    ParserLambda -.->|"Return suggested agenda"| User

    %% Save flow
    User -->|"4. [SAVE] POST edited agenda + suggestion"| BackendAPI
    BackendAPI -->|"Persist agenda + ai_suggestion"| AuroraDB
```

### Flow Descriptions
1. **Parse Flow (Suggest)**: The user pastes free text in the browser. The browser sends `{ text, today, tz }` with the user's Cognito JWT directly to the Agenda Parser Lambda Function URL (outside the VPC). The parser calls Claude on Amazon Bedrock over the public internet, validates the structured output via the `record_agenda` tool, and returns the suggested agenda JSON to the browser.
2. **Save Flow (Decide)**: The user reviews and edits the pre-filled fields. When the user clicks **Save**, the browser submits the final agenda along with the model's original suggestion (`ai_suggestion`, `model`, `prompt_version`) to the main backend API, which validates and stores it in the Aurora PostgreSQL database. The AI model never writes directly to the database.
