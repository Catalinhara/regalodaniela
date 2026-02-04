import asyncpg
import asyncio


async def test_credentials():
    """Test common PostgreSQL credentials and create the companion database if needed."""
    
    # Common credential combinations for Odoo PostgreSQL installations
    cred_combinations = [
        ("postgres", "postgres"),
        ("postgres", "admin"),
        ("postgres", ""),
        ("odoo", "odoo"),
        ("user", "password"),
        ("user", "user"),
    ]
    
    working_creds = None
    
    print("Testing PostgreSQL credentials...")
    print("=" * 50)
    
    for username, password in cred_combinations:
        try:
            print(f"\nTrying: {username} / {'(empty)' if password == '' else '*' * len(password)}")
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                user=username,
                password=password,
                database="postgres"  # Connect to default postgres db first
            )
            print(f"✓ SUCCESS! Working credentials: {username}")
            working_creds = (username, password)
            
            # Check if companion database exists
            databases = await conn.fetch("SELECT datname FROM pg_database WHERE datname='companion'")
            
            if databases:
                print(f"✓ Database 'companion' already exists")
            else:
                print(f"Creating database 'companion'...")
                await conn.execute("CREATE DATABASE companion")
                print(f"✓ Database 'companion' created successfully")
            
            await conn.close()
            break
            
        except asyncpg.exceptions.InvalidPasswordError:
            print(f"✗ Authentication failed")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
    
    if working_creds:
        username, password = working_creds
        print("\n" + "=" * 50)
        print("DATABASE SETUP SUCCESSFUL!")
        print("=" * 50)
        print(f"\nWorking credentials: {username} / {password if password else '(empty password)'}")
        print(f"\nDatabase URL for backend:")
        print(f"postgresql+asyncpg://{username}:{password}@localhost:5432/companion")
        print(f"\nNext steps:")
        print(f"1. Create a .env file in the backend directory with:")
        print(f"   DATABASE_URL=postgresql+asyncpg://{username}:{password}@localhost:5432/companion")
        print(f"2. Restart the backend server")
        return True
    else:
        print("\n" + "=" * 50)
        print("FAILED TO FIND WORKING CREDENTIALS")
        print("=" * 50)
        print("\nNo working credentials found. Please provide the correct PostgreSQL password.")
        print("You may need to reset the PostgreSQL password or check Odoo's configuration.")
        return False


if __name__ == "__main__":
    asyncio.run(test_credentials())
