# docker/sandbox-python/Dockerfile
# Hardened, Micro-Isolated Python Execution Sandbox Container
FROM python:3.11-slim-bookworm

# Create unprivileged execution group and user (UID 10001)
RUN groupadd -g 10001 sandboxgroup && \
    useradd -u 10001 -g sandboxgroup -s /bin/false -m sandboxuser

# Install standard offline data analysis packages
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2 \
    openpyxl==3.1.2 \
    scipy==1.13.0 \
    matplotlib==3.8.4

# Prepare isolated workspace structure
WORKDIR /workspace
RUN mkdir -p /workspace/input /workspace/output /tmp && \
    chown -R sandboxuser:sandboxgroup /workspace /tmp && \
    chmod 700 /workspace /tmp

USER 10001:10001

ENTRYPOINT ["python", "-u"]
