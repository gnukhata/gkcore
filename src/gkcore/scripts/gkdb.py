import sys
from dotenv import load_dotenv
from gkcore.migrations.initdb import load_initial_data, create_tables
from gkcore.migrations.db_migrate import migrate

load_dotenv()

def main():
    """Command to handle database init and migrate

    Usage: `gkdb [--init | --migrate]`

    - `init` will initialise database
    - `migrate` will migrate the database changes
    """

    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--init":
            create_tables()
            print("Created tables.")
            load_initial_data()
            print("Added initial data.")
        elif arg == "--migrate":
            migrate()
            print("Migration complete.")
        else:
            print("Unknown argument:", arg)
            print("Usage: gkdb [--init | --migrate]")
            sys.exit(1)
    else:
        print("No argument provided.")
        print("Usage: gkdb [init | migrate]")

    sys.exit(0)


if __name__ == "__main__":
    main()
