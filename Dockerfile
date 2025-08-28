# Stage 1: Install AWS Lambda Web Adapter
FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 as adapter

# Stage 2: Build the application
FROM python:3.12-slim as builder

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency definition and install dependencies
COPY pyproject.toml .
RUN uv pip install --system --no-cache --requirement pyproject.toml

# Copy application code
COPY src/try_aws_lambda_web_adapter/ /app/

# Stage 3: Final image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY --from=builder /app/ /app/

# Copy AWS Lambda Web Adapter
COPY --from=adapter /lambda-adapter /opt/extensions/lambda-adapter

# Set environment variables for Lambda Web Adapter
# AWS_LAMBDA_RUNTIME_API is automatically set by the Lambda runtime environment.
# Setting it here is good for local testing but not required for deployment.
ENV AWS_LAMBDA_WEB_ADAPTER_PORT=8080

# Define the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
