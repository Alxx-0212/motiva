#!/bin/bash
set -e

echo "[INFO] Starting database initialization..."

# Create chainlit database
createdb -U $POSTGRES_USER chainlit_db

# Restore the dump file using pg_restore 
if [ -f /docker-entrypoint-initdb.d/200925_data.dump ]; then
    echo "[INFO] Restoring database from dump file..."
    pg_restore \
        -v \
        --no-owner \
        --no-privileges \
        -U $POSTGRES_USER \
        -d $POSTGRES_DB \
        /docker-entrypoint-initdb.d/200925_data.dump
    echo "[SUCCESS] Database restored from dump file"
fi

if [ -f /docker-entrypoint-initdb.d/chainlit_db_data.dump ]; then
    echo "[INFO] Restoring database from dump file..."
    pg_restore \
        -v \
        --no-owner \
        --no-privileges \
        -U $POSTGRES_USER \
        -d $CHAINLIT_DB \
        /docker-entrypoint-initdb.d/chainlit_db_data.dump
    echo "[SUCCESS] Database restored from dump file"
fi

echo "[SUCCESS] Database initialization completed"