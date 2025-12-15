from src.codeguardian.tools.tools import ensure_repo_indexed

def main():
    # force=True -> always rebuild/update index now
    msg = ensure_repo_indexed(force=True)
    print(msg)

if __name__ == "__main__":
    main()
