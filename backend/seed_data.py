import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.infrastructure.tables import Base, UserModel, CompanionContextModel, PatientModel, ColleagueModel, EventModel, CheckInModel
from app.infrastructure.auth import get_password_hash
from app.domain.models import CheckInIntent, MoodState

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/companion")
USER_EMAIL = "catalinohara@gmail.com"
USER_PASS = "Password123!"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

import argparse

async def reset_database():
    print("--- Resetting Database (Nuclear Reset) ---")
    async with engine.begin() as conn:
        # Drop all tables manually to ensure clean state
        await conn.execute(text("DROP TABLE IF EXISTS insights CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS chat_messages CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS chat_conversations CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS events CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS colleagues CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS patients CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS check_ins CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS companion_contexts CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS refresh_tokens CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    
    print("Running migrations...")
    # Adjust path if needed for different OS
    alembic_path = os.path.join(os.getcwd(), "venv", "Scripts", "alembic")
    if not os.path.exists(alembic_path):
        alembic_path = "alembic" # Fallback to path
        
    try:
        subprocess.run([alembic_path, "upgrade", "head"], check=True)
        print("Database schema built successfully.")
    except Exception as e:
        print(f"Migration error: {e}. Trying simple create_all...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def seed_data(reset=False):
    if reset:
        await reset_database()

    async with AsyncSessionLocal() as db:
        print(f"--- Seeding High-Complexity Clinical Environment ---")
        
        # 1. Check if user already exists
        from app.infrastructure.tables import UserModel
        user_stmt = select(UserModel).where(UserModel.email == USER_EMAIL)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        if not user:
            print(f"Creating new user: {USER_EMAIL}")
            hashed_pw = get_password_hash(USER_PASS)
            user = UserModel(
                id=uuid4(),
                email=USER_EMAIL,
                hashed_password=hashed_pw,
                full_name="Cata",
                language="es",
                onboarding_completed=True,
                professional_role="Psicólogo Clínico - Hospital de Día Infantil",
                years_experience=10,
                primary_stressor="Entorno laboral tóxico y carga clínica de alta gravedad",
                coping_style="Reflexivo y Analítico con tendencia a la rumiación"
            )
            db.add(user)
            await db.flush()
        else:
            print(f"User {USER_EMAIL} already exists. Seeding data for this user.")
        
        # 2. Initial Companion Context (Simulating a heavy week)
        # Check if context already exists
        context_stmt = select(CompanionContextModel).where(CompanionContextModel.user_id == user.id)
        context_res = await db.execute(context_stmt)
        context = context_res.scalar_one_or_none()
        
        if not context:
            context = CompanionContextModel(
                user_id=user.id, 
                current_mood="DRAINED", 
                current_energy=3
            )
            db.add(context)
        
        # 3. Severe Pediatric Patients
        # Clear existing patients for this user to avoid duplicates if re-seeding
        # (Optional: depends on if we want additive or clean seed)
        # For a clean test environment, let's clear existing patients/events for this user
        await db.execute(text(f"DELETE FROM patients WHERE user_id = '{user.id}'"))
        await db.execute(text(f"DELETE FROM events WHERE user_id = '{user.id}'"))
        await db.execute(text(f"DELETE FROM colleagues WHERE user_id = '{user.id}'"))
        await db.execute(text(f"DELETE FROM check_ins WHERE user_id = '{user.id}'"))

        print("Adding Heavy Clinical Load (Patients)...")
        # ... (Rest of the patient/event/check-in creation logic remains the same)
        patients = [
            PatientModel(
                user_id=user.id, alias="Leo (P-202)", emotional_load=10, trend="declining",
                description="TEA Grado 3. Crisis de agresividad graves dirigidas al personal. Inestabilidad sensorial extrema.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=60)
            ),
            PatientModel(
                user_id=user.id, alias="Sofía (P-203)", emotional_load=9, trend="stable",
                description="Depresión mayor infantil precoz. Ideación suicida activa. Historial de autolesiones constantes.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=30)
            ),
            PatientModel(
                user_id=user.id, alias="Marc (P-204)", emotional_load=8, trend="declining",
                description="Trastorno disocial de la conducta. Oposicionismo extremo y fugas del hospital de día.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=90)
            ),
            PatientModel(
                user_id=user.id, alias="Lucía (P-205)", emotional_load=9, trend="declining",
                description="Brote psicótico en evolución. Alucinaciones auditivas y desorganización en el grupo de terapia.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=15)
            ),
            PatientModel(
                user_id=user.id, alias="Hugo (P-206)", emotional_load=7, trend="improving",
                description="Mutismo selectivo tras trauma familiar complejo. Empieza a emitir sonidos, pero muy vulnerable.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=120)
            ),
            PatientModel(
                user_id=user.id, alias="Elena (P-207)", emotional_load=10, trend="declining",
                description="TCA restrictivo grave. Rechazo absoluto a la comida en sala. Riesgo inminente de ingreso hospitalario total.",
                therapy_start_date=datetime.utcnow().date() - timedelta(days=10)
            ),
        ]
        db.add_all(patients)
        await db.flush()
        
        # 4. Toxic Team (Colleagues)
        print("Adding Toxic Team Dynamics (Colleagues)...")
        colleagues = [
            ColleagueModel(user_id=user.id, name="Dra. Vanesa (Psiquiatra)", relationship_type="Jefa Narcisista (Hostil)"),
            ColleagueModel(user_id=user.id, name="Miguel (Psicólogo)", relationship_type="Compañero Sumiso (Bloqueado)"),
            ColleagueModel(user_id=user.id, name="Clara (Enfermería)", relationship_type="Personal de Sala (Agotada)"),
            ColleagueModel(user_id=user.id, name="Pedro (Terapeuta Ocup.)", relationship_type="Personal de Sala (Frustrado)"),
        ]
        db.add_all(colleagues)
        await db.flush()
        
        # 5. Stressful Life & Work Events
        print("Adding High-Impact Events...")
        events = [
            EventModel(user_id=user.id, title="Auditoría de Acreditación Sanitaria", event_date=datetime.utcnow() + timedelta(days=7), impact_level=10),
            EventModel(user_id=user.id, title="Presentación de Resultados a Dirección", event_date=datetime.utcnow() + timedelta(days=2), impact_level=9),
            EventModel(user_id=user.id, title="Crisis Familiar (Problema de salud grave)", event_date=datetime.utcnow() + timedelta(days=5), impact_level=10),
            EventModel(user_id=user.id, title="Reunión de Equipo Conflictiva (Vanesa)", event_date=datetime.utcnow() + timedelta(days=1), impact_level=8),
            EventModel(user_id=user.id, title="Supervisión Externa Individual", event_date=datetime.utcnow() + timedelta(days=14), impact_level=6),
        ]
        db.add_all(events)
        await db.flush()
        
        # 6. Check-ins: Professional and Personal History (Spanish Priority)
        print("Generating Realistic Check-ins Context...")
        history_history = [
            { "type": "COLLEAGUE", "id": colleagues[0].id, "intent": CheckInIntent.RELEASE, "mood": MoodState.FRUSTRATED, "text": "Vanesa me ha corregido el informe clínico de Elena de mala manera delante de todo el equipo." },
            { "type": "PATIENT", "id": patients[0].id, "intent": CheckInIntent.RELEASE, "mood": MoodState.DRAINED, "text": "Leo ha tenido una crisis de 40 minutos. He tenido que contenerlo emocionalmente y estoy agotado físicamente." },
            { "type": "PATIENT", "id": patients[2].id, "intent": CheckInIntent.TRACK, "mood": MoodState.ANXIOUS, "text": "Marc ha vuelto a amenazar con escaparse. La vigilancia en el patio debe reforzarse." },
            { "type": "COLLEAGUE", "id": colleagues[1].id, "intent": CheckInIntent.TRACK, "mood": MoodState.DRAINED, "text": "Miguel no se atreve a decir nada en las reuniones. Siento que estoy solo defendiendo a los pacientes." },
            { "type": "PATIENT", "id": patients[5].id, "intent": CheckInIntent.SEEK_VALIDATION, "mood": MoodState.FRUSTRATED, "text": "Elena no ha comido nada hoy tampoco. La Dra. Vanesa culpa a mi enfoque terapéutico por la falta de peso." },
            { "type": "PATIENT", "id": patients[4].id, "intent": CheckInIntent.SEEK_CLARITY, "mood": MoodState.CALM, "text": "Hugo ha jugado 10 minutos con las piezas de madera. Sin habla, pero ha mantenido contacto visual breve." },
            { "type": "PATIENT", "id": patients[3].id, "intent": CheckInIntent.TRACK, "mood": MoodState.ANXIOUS, "text": "Lucía está empezando a oír voces de nuevo. El ambiente en el comedor hoy era de tensión absoluta." },
            { "type": "COLLEAGUE", "id": colleagues[0].id, "intent": CheckInIntent.SEEK_DISTANCE, "mood": MoodState.DRAINED, "text": "Vanesa ha vuelto a gritar en el control. Necesito poner distancia o me voy a quemar definitivamente." },
            { "type": "PATIENT", "id": patients[1].id, "intent": CheckInIntent.RELEASE, "mood": MoodState.DRAINED, "text": "Sofía ha traído cortes nuevos en las muñecas. Me siento impotente ante tanto sufrimiento infantil." },
        ]

        for i, entry in enumerate(history_history):
            ts = datetime.utcnow() - timedelta(days=(9-i), hours=4)
            db.add(CheckInModel(
                user_id=user.id,
                timestamp=ts,
                context_type=entry['type'],
                context_id=str(entry['id']),
                intent=entry['intent'].value,
                mood_state=entry['mood'].value,
                energy_level=3,
                text_content=entry['text']
            ))

        await db.commit()
        print("--- Exhaustive Clinical Seed Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed ClaraMente DB")
    parser.add_argument("--reset", action="store_true", help="Perform a nuclear reset before seeding")
    parser.add_argument("--email", type=str, help="Target email to seed (defaults to seed_data.py config)", default=USER_EMAIL)
    args = parser.parse_args()
    
    # Overwrite global USER_EMAIL if provided
    USER_EMAIL = args.email

    async def main():
        await seed_data(reset=args.reset)
    
    asyncio.run(main())
