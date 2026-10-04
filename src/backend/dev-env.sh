# Chạy từ src/backend: source dev-env.sh
# Kích hoạt Python và thêm PostgreSQL local vào PATH của terminal hiện tại.
if [ ! -f pyproject.toml ] || [ ! -f .venv/bin/activate ]; then
    echo "Hãy cd vào src/backend trước khi chạy: source dev-env.sh"
    return 1
fi

. .venv/bin/activate

if [ -d "$PWD/.postgresql/bin" ]; then
    export PATH="$PWD/.postgresql/bin:$PATH"
fi
