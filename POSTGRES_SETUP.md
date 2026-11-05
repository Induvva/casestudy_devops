# PostgreSQL deployment

The application now requires PostgreSQL; it no longer falls back to SQLite.
`db.py` connects using `DATABASE_URL` when set, or the standard PostgreSQL
environment variables (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and
`PGPASSWORD`). The Kubernetes app deployment already sets these values and
reads the password from the `tripplanner-db` Secret.

## Connect to local PostgreSQL

Make sure PostgreSQL is running, then create a local environment file and set
the password for your PostgreSQL user in it. `.env` is ignored by Git.

```powershell
Copy-Item .env.example .env
notepad .env
```

The example connects to `localhost:5432` as `postgres` and uses the database
`tripplanner`. Update these values in `.env` if your local PostgreSQL settings
differ. Create the database if it does not exist yet:

```powershell
createdb -h localhost -p 5432 -U postgres tripplanner
```

Verify the connection before creating any application tables:

```powershell
python -c "from db import connect; c = connect(); q = c.cursor(); q.execute('SELECT current_database(), current_user'); print(q.fetchone()); c.close()"
```

This should print the connected database and user. Connection errors are
reported by psycopg; check that PostgreSQL is running and that the `.env`
settings match your installation.

## Set the PostgreSQL password Secret

For the development password, create or update the Kubernetes Secret without
writing the password into this file or shell history:

```powershell
$secret = Read-Host "Enter the PostgreSQL password" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    kubectl create secret generic tripplanner-db "--from-literal=password=$password" --dry-run=client -o yaml | kubectl apply -f -
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    Remove-Variable password, secret, ptr -ErrorAction SilentlyContinue
}
```

The requested password is weak and intended only for development. Kubernetes
Secrets are not automatically encrypted in every cluster. If PostgreSQL has
already initialized its persistent volume with a different password, changing
the Secret alone does not update the database role. Connect to PostgreSQL and
use psql's password prompt:

```powershell
kubectl exec -it statefulset/tripplanner-postgres -- psql -U tripplanner -d tripplanner
```

At the `psql` prompt, run `\password tripplanner`, enter the requested password
twice, then run `\q`. Restart the app so its environment picks up the updated
Secret:

```powershell
kubectl rollout restart deployment/tripplanner-deployment
```

## Build and deploy

```powershell
docker build -t tripplanner:v2 .
kubectl apply -f postgres.yaml
kubectl rollout status statefulset/tripplanner-postgres
kubectl apply -f deployment.yaml
kubectl rollout status deployment/tripplanner-deployment
```

## Run the Jenkins pipeline

The Jenkins agent must have Python 3, Docker, and `kubectl`, and must use the
`docker-desktop` Kubernetes context. Create the `tripplanner-db` Secret in that
cluster before running the job; the pipeline checks for it and does not store
or create database credentials. The pipeline installs dependencies, validates
Python syntax, builds the image, checks that `.env` is not in the image, applies
the PostgreSQL and app manifests, waits for both rollouts, and verifies the
app's PostgreSQL connection and `users` table.

Run the Jenkins job from the repository root. Each successful run deploys the
new `tripplanner:v2` image to the Docker Desktop cluster. Jenkins runs builds
sequentially because they share this local image and cluster.

The PostgreSQL manifest requests a 1 GiB volume from the cluster's default
StorageClass. For production, use a managed PostgreSQL service, backups, and
appropriate resource limits.
