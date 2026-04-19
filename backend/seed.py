import asyncio
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.event import Event
from app.utils.dedup import save_events
from app.schemas.event import EventCreate

async def seed_data():
    print("Seeding sample data...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sample_events = [
        EventCreate(
            title="Stripe Sessions 2026: The Future of Money",
            description="Join us for the keynote event of Stripe Sessions, where we'll announce new products and discuss the future of the global economy.",
            platform="Eventbrite",
            platform_event_id="eb_stripe_2026",
            url="https://www.eventbrite.com/e/stripe-sessions-2026-tickets-1234567890",
            start_time=datetime.now() + timedelta(days=5),
            city="San Francisco",
            location="Moscone Center",
            is_free=False,
            image_url="https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&q=80&w=800"
        ),
        EventCreate(
            title="Rust Meetup: Performance Optimization",
            description="Deep dive into memory management and benchmarking in Rust. Sponsored by Razorpay.",
            platform="Meetup",
            platform_event_id="mu_rust_blr",
            url="https://www.meetup.com/rust-bangalore/events/987654321/",
            start_time=datetime.now() + timedelta(days=2),
            city="Bangalore",
            location="Razorpay HQ, Koramangala",
            is_free=True,
            image_url="https://images.unsplash.com/photo-1515187029135-18ee286d815b?auto=format&fit=crop&q=80&w=800"
        ),
        EventCreate(
            title="London AI Summit 2026",
            description="A gathering of the top minds in artificial intelligence, focusing on large-scale generative models and safety.",
            platform="Eventbrite",
            platform_event_id="eb_ai_london",
            url="https://www.eventbrite.co.uk/e/london-ai-summit-2026-tickets-0987654321",
            start_time=datetime.now() + timedelta(days=10),
            city="London",
            location="ExCeL London",
            is_free=False,
            image_url="https://images.unsplash.com/photo-1514328537541-ad4611ba05f5?auto=format&fit=crop&q=80&w=800"
        )
    ]

    async with AsyncSessionLocal() as db:
        await save_events(db, sample_events)
    
    print("Seed completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
