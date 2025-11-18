FROM python:3.12-slim

# Install system dependencies for all checkers
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Spell checking
    aspell \
    aspell-en \
    # LaTeX linting
    chktex \
    # LanguageTool (Java-based grammar checker)
    default-jre-headless \
    wget \
    unzip \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install LanguageTool
RUN wget -q https://languagetool.org/download/LanguageTool-stable.zip -O /tmp/lt.zip \
    && unzip -q /tmp/lt.zip -d /opt \
    && mv /opt/LanguageTool-* /opt/languagetool \
    && rm /tmp/lt.zip \
    # Create wrapper script so 'languagetool' command works
    && echo '#!/bin/bash\njava -jar /opt/languagetool/languagetool-commandline.jar "$@"' > /usr/local/bin/languagetool \
    && chmod +x /usr/local/bin/languagetool

# Set working directory
WORKDIR /app

# Copy and install CheckMyTex package (context is parent directory)
COPY . /checkmytex
RUN pip install --no-cache-dir /checkmytex

# Copy web app files
COPY web_app /app

# Install web app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run the app
# Note: LanguageTool runs on-demand via the Languagetool checker
CMD ["python", "app.py"]
