import os
import sys
import subprocess
import time

# Configura encoding UTF-8 no stdout no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def setup_venv():
    """Garante que o script esteja executando dentro de um ambiente virtual (venv).
    Caso o venv não exista, cria e instala as dependências.
    Se já existe, reinicia o script usando o Python do venv.
    """
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv")
    in_venv = sys.prefix != sys.base_prefix

    if not in_venv:
        venv_exists = os.path.exists(venv_dir)

        if sys.platform == "win32":
            python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_executable = os.path.join(venv_dir, "bin", "python")
            pip_executable = os.path.join(venv_dir, "bin", "pip")

        if not venv_exists:
            print("[VENV] Ambiente virtual (.venv) não encontrado. Criando...")
            try:
                subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
                print("[VENV] Ambiente virtual criado com sucesso.")

                requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
                if os.path.exists(requirements_path):
                    print("[VENV] Instalando dependências (requirements.txt)...")
                    subprocess.run([pip_executable, "install", "-r", requirements_path], check=True)
                    print("[VENV] Dependências instaladas com sucesso.")
            except Exception as e:
                print(f"[VENV] [ERRO] Falha ao criar ou preparar o venv: {e}")
                sys.exit(1)

        print("[VENV] Ativando ambiente virtual e reiniciando script...")
        try:
            result = subprocess.run([python_executable] + sys.argv)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"[VENV] [ERRO] Falha ao reiniciar o script no venv: {e}")
            sys.exit(1)


def run_command(command: str) -> bool:
    """Executa um comando no shell e exibe o output em tempo real."""
    print(f"\n[EXEC] Running: {command}...")
    try:
        result = subprocess.run(command, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] O comando falhou com o erro: {e}")
        return False


def wait_for_db(timeout: int = 60) -> bool:
    """Aguarda até que o PostgreSQL esteja pronto para aceitar conexões."""
    print("\n⌛ Aguardando o banco de dados PostgreSQL ficar pronto...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                "docker-compose exec -T postgres pg_isready -U rapidao_user -d rapidao_db",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                print("❇️  Banco de dados está pronto!")
                return True
        except Exception:
            pass
        time.sleep(2)
    print("❌ Timeout: O banco de dados não ficou pronto a tempo.")
    return False


def wait_for_redis(timeout: int = 30) -> bool:
    """Aguarda até que o Redis esteja pronto."""
    print("\n⌛ Aguardando o Redis ficar pronto...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                "docker-compose exec -T redis redis-cli ping",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                print("❇️  Redis está pronto!")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("❌ Timeout: O Redis não ficou pronto a tempo.")
    return False


def start_project():
    """Sobe todos os containers, aplica migrações e inicializa a aplicação completa."""
    print("=" * 60)
    print("🚀 INICIALIZANDO O RAPIDÃO — DELIVERY & LOGÍSTICA")
    print("=" * 60)

    # 1. Build e subida dos containers
    print("\nStep 1: Subindo os containers no Docker...")
    if not run_command("docker-compose up --build -d"):
        print("\n❌ Falha ao iniciar os containers. Verifique se o Docker Desktop está rodando.")
        return

    # 2. Aguarda banco de dados e Redis
    print("\nStep 2: Aguardando estabilização dos serviços de infraestrutura...")
    db_ok = wait_for_db()
    redis_ok = wait_for_redis()

    if not db_ok:
        print("\n⚠️  Alerta: PostgreSQL demorou para responder. Tentando continuar mesmo assim...")
    if not redis_ok:
        print("\n⚠️  Alerta: Redis demorou para responder. Tentando continuar mesmo assim...")

    # 3. Aplica migrações do Alembic
    print("\nStep 3: Aplicando migrações do banco de dados (Alembic)...")
    if not run_command("docker-compose exec -T app alembic upgrade head"):
        print("\n⚠️  Falha ao rodar migrações no container. Tentando localmente...")
        if not run_command("alembic upgrade head"):
            print("\n❌ Falha crítica: Migrações não puderam ser aplicadas.")
            print("Execute manualmente: python run.py migrate")

    # 4. Status dos containers
    print("\nStep 4: Verificando status dos serviços...")
    run_command("docker ps")

    print("\n" + "=" * 60)
    print("🎉 Rapidão iniciado com sucesso!")
    print("  📖 Swagger UI:   http://localhost:8000/docs")
    print("  📋 ReDoc:        http://localhost:8000/redoc")
    print("  🐘 PostgreSQL:   localhost:5433")
    print("  🔴 Redis:        localhost:6380")
    print("  🐘 pgAdmin 4:    http://localhost:8081 (admin@rapidao.com / admin123)")
    print("=" * 60)

    # 5. Logs em tempo real
    show_logs()


def stop_project():
    """Para e remove todos os containers da aplicação."""
    print("=" * 60)
    print("🛑 PARANDO O RAPIDÃO")
    print("=" * 60)
    run_command("docker-compose down")
    print("\n✅ Todos os containers foram desligados.")


def stop_and_clean():
    """Para containers e remove volumes (apaga dados do banco)."""
    print("=" * 60)
    print("🧹 PARANDO E LIMPANDO O RAPIDÃO (volumes incluídos)")
    print("=" * 60)
    confirm = input("⚠️  Isso apagará todos os dados do banco! Confirmar? (s/N): ").strip().lower()
    if confirm == "s":
        run_command("docker-compose down -v")
        print("\n✅ Containers e volumes removidos.")
    else:
        print("\nOperação cancelada.")


def run_migrations():
    """Aplica as migrações do Alembic (dentro do container ou localmente)."""
    print("\n🔄 Aplicando migrações do Alembic...")
    if not run_command("docker-compose exec -T app alembic upgrade head"):
        print("Tentando rodar migrações localmente...")
        run_command("alembic upgrade head")


def run_tests():
    """Executa a suíte de testes automatizados com Docker Compose de testes."""
    print("\n🧪 Executando testes automatizados (docker-compose.test.yml)...")
    run_command("docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit")
    run_command("docker-compose -f docker-compose.test.yml down -v")


def show_logs():
    """Acompanha os logs de todos os serviços em tempo real."""
    print("\n📋 Exibindo logs em tempo real (CTRL+C para sair)...")
    try:
        run_command("docker-compose logs -f")
    except KeyboardInterrupt:
        print("\nSaindo da visualização de logs.")


def show_logs_service(service: str):
    """Exibe os logs de um serviço específico."""
    print(f"\n📋 Logs do serviço '{service}' (CTRL+C para sair)...")
    try:
        subprocess.run(f"docker-compose logs -f {service}", shell=True)
    except KeyboardInterrupt:
        print("\nSaindo da visualização de logs.")


def show_status():
    """Mostra o status atual de todos os containers."""
    print("\n📊 Status atual dos containers:")
    run_command("docker ps")


def main():
    actions = {
        "start":   ("Iniciar/Buildar Projeto completo (Docker + Migrações)", start_project),
        "stop":    ("Parar todos os containers", stop_project),
        "clean":   ("Parar containers e apagar volumes (reset total)", stop_and_clean),
        "migrate": ("Aplicar migrações do Alembic", run_migrations),
        "test":    ("Executar suíte de testes automatizados", run_tests),
        "logs":    ("Ver logs de todos os serviços em tempo real", show_logs),
        "status":  ("Ver status dos containers", show_status),
    }

    if len(sys.argv) < 2:
        print("=" * 60)
        print("🚀 RAPIDÃO — Script de Gerenciamento")
        print("=" * 60)
        print("\nUso: python run.py [comando]\n")
        print("Comandos disponíveis:")
        for cmd, (desc, _) in actions.items():
            print(f"  {cmd:<10} {desc}")

        # Menu interativo
        print("\nOu escolha pelo menu interativo:")
        for i, (cmd, (desc, _)) in enumerate(actions.items(), 1):
            print(f"  {i}. {desc}")

        try:
            choice = input("\nEscolha uma opção (1-7): ").strip()
            keys = list(actions.keys())
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                _, fn = actions[keys[idx]]
                fn()
            else:
                print("Opção inválida.")
        except (KeyboardInterrupt, EOFError, ValueError):
            print("\nSaindo...")
        return

    action = sys.argv[1].lower()

    # Suporte a: python run.py logs app
    if action == "logs" and len(sys.argv) == 3:
        show_logs_service(sys.argv[2])
        return

    if action in actions:
        _, fn = actions[action]
        fn()
    else:
        print(f"Ação desconhecida: '{action}'")
        print(f"Ações válidas: {', '.join(actions.keys())}")


if __name__ == "__main__":
    setup_venv()
    main()
