import asyncio
from bot.database.database import async_session_maker
from bot.database.models import Payment, Driver
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        # Find all pending payments
        stmt = select(Payment).where(Payment.status.in_(["PENDING", "PENDING_RENEWAL"]))
        res = await session.execute(stmt)
        payments = res.scalars().all()
        
        fixed_count = 0
        for p in payments:
            # check the driver's status
            driver_res = await session.execute(select(Driver).where(Driver.id == p.driver_id))
            driver = driver_res.scalar_one_or_none()
            if driver:
                if driver.status == "APPROVED" and driver.payment_status == "APPROVED":
                    p.status = "APPROVED"
                    fixed_count += 1
                elif driver.status == "REJECTED":
                    p.status = "REJECTED"
                    fixed_count += 1
                    
        await session.commit()
        print(f"Fixed {fixed_count} ghost pending payments.")

if __name__ == "__main__":
    asyncio.run(main())
