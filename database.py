"""
Модуль для работы с базой данных
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, select, func, and_, Date, cast
from datetime import datetime, timedelta, date

import config

Base = declarative_base()

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    name = Column(String(200))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Subscription(Base):
    """Модель абонемента"""
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    subscription_type = Column(String(50))  # one_group, all_groups
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    trainings_left = Column(Integer, default=8)


class Training(Base):
    """Модель тренировки"""
    __tablename__ = 'trainings'

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    description = Column(String(1000))
    trainer = Column(String(200))
    day_of_week = Column(Integer)  # 0-6 (понедельник-воскресенье)
    time = Column(String(10))
    duration = Column(Integer, default=60)  # в минутах
    max_participants = Column(Integer, default=10)
    training_type = Column(String(50))  # online, studio


class Booking(Base):
    """Модель записи на тренировку"""
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    training_id = Column(Integer, ForeignKey('trainings.id'))
    booking_date = Column(DateTime)
    status = Column(String(20), default='active')  # active, cancelled, completed
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Модель платежа"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    amount = Column(Float)
    payment_type = Column(String(50))
    status = Column(String(20), default='pending')  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)


class Visit(Base):
    """Модель посещения"""
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    training_id = Column(Integer, ForeignKey('trainings.id'))
    visit_date = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Получение сессии базы данных"""
    async with async_session() as session:
        return session


async def get_user(user_id: int):
    """Получение данных пользователя по user_id"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return {
                'name': user.name,
                'username': user.username,
                'reg_date': user.created_at.isoformat() if user.created_at else None,
                'user_id': user.user_id
            }
        return None


async def get_active_subscription(user_id: int):
    """Получение активного абонемента пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            return {
                'type': sub.subscription_type,
                'start_date': sub.start_date.strftime('%Y-%m-%d') if sub.start_date else None,
                'end_date': sub.end_date.strftime('%Y-%m-%d') if sub.end_date else None,
                'is_active': sub.is_active
            }
        return None


async def get_all_clients():
    """Получение списка всех клиентов с абонементами"""
    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        users = result.scalars().all()

        clients = []
        for user in users:
            sub_result = await session.execute(
                select(Subscription).where(
                    Subscription.user_id == user.user_id,
                    Subscription.is_active == True
                )
            )
            sub = sub_result.scalar_one_or_none()

            clients.append({
                'name': user.name,
                'username': user.username,
                'user_id': user.user_id,
                'sub_type': sub.subscription_type if sub else None,
                'end_date': sub.end_date.strftime('%d.%m.%Y') if sub and sub.end_date else None
            })

        return clients


async def get_sales_stats():
    """Статистика продаж за текущий месяц"""
    async with async_session() as session:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        result = await session.execute(
            select(
                func.sum(Payment.amount),
                func.count(Payment.id)
            ).where(
                Payment.status == 'confirmed',
                Payment.created_at >= month_start
            )
        )
        row = result.one()

        return {
            'total_income': row[0] or 0,
            'total_sales': row[1] or 0
        }


async def get_user_payments(user_id: int):
    """Получение истории платежей пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.user_id == user_id
            ).order_by(Payment.created_at.desc())
        )
        payments = result.scalars().all()

        return [
            {
                'id': p.id,
                'amount': p.amount,
                'payment_type': p.payment_type,
                'status': p.status,
                'created_at': p.created_at,
                'confirmed_at': p.confirmed_at
            }
            for p in payments
        ]


async def get_user_visits(user_id: int):
    """Получение истории посещений пользователя"""
    async with async_session() as session:
        result = await session.execute(
            select(Visit, Training).join(
                Training, Visit.training_id == Training.id
            ).where(
                Visit.user_id == user_id
            ).order_by(Visit.visit_date.desc())
        )
        visits = result.all()

        return [
            {
                'visit_date': v.Visit.visit_date,
                'training_name': v.Training.name,
                'trainer': v.Training.trainer
            }
            for v in visits
        ]


async def get_users_for_broadcast(segment: str = 'all'):
    """Получение списка пользователей для рассылки по сегменту"""
    async with async_session() as session:
        if segment == 'all':
            # Все пользователи
            result = await session.execute(
                select(User.user_id).where(User.is_active == True)
            )
        elif segment == 'with_sub':
            # Только с активным абонементом
            result = await session.execute(
                select(User.user_id).join(
                    Subscription, User.user_id == Subscription.user_id
                ).where(
                    User.is_active == True,
                    Subscription.is_active == True
                )
            )
        elif segment == 'without_sub':
            # Без абонемента
            subquery = select(Subscription.user_id).where(Subscription.is_active == True)
            result = await session.execute(
                select(User.user_id).where(
                    User.is_active == True,
                    ~User.user_id.in_(subquery)
                )
            )
        else:
            result = await session.execute(
                select(User.user_id).where(User.is_active == True)
            )

        return [row[0] for row in result.all()]


async def get_detailed_sales_stats():
    """Детальная статистика продаж по типам продуктов"""
    async with async_session() as session:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Получаем все подтверждённые платежи за месяц
        result = await session.execute(
            select(Payment).where(
                Payment.status == 'confirmed',
                Payment.created_at >= month_start
            )
        )
        payments = result.scalars().all()

        # Группируем по типу продукта
        stats_by_type = {}
        total_income = 0
        total_count = 0

        for p in payments:
            p_type = p.payment_type or 'other'
            if p_type not in stats_by_type:
                stats_by_type[p_type] = {'count': 0, 'amount': 0}
            stats_by_type[p_type]['count'] += 1
            stats_by_type[p_type]['amount'] += p.amount or 0
            total_income += p.amount or 0
            total_count += 1

        # Общее количество клиентов
        users_result = await session.execute(select(func.count(User.id)))
        total_users = users_result.scalar() or 0

        # Клиенты с активным абонементом
        active_subs_result = await session.execute(
            select(func.count(Subscription.id)).where(Subscription.is_active == True)
        )
        active_subscriptions = active_subs_result.scalar() or 0

        return {
            'total_income': total_income,
            'total_sales': total_count,
            'by_type': stats_by_type,
            'total_users': total_users,
            'active_subscriptions': active_subscriptions
        }


async def seed_trainings():
    """Заполнить таблицу Training 19 записями расписания (идемпотентно)"""
    schedule = [
        # Силовая — тренер Анна
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 0, "time": "08:30", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 0, "time": "17:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 0, "time": "18:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 2, "time": "08:30", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 2, "time": "17:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 2, "time": "18:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 4, "time": "08:30", "max_participants": 28},
        {"name": "Силовая", "trainer": "Анна", "day_of_week": 4, "time": "17:10", "max_participants": 28},
        # Силовая — тренер Алена
        {"name": "Силовая", "trainer": "Алена", "day_of_week": 0, "time": "19:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Алена", "day_of_week": 0, "time": "20:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Алена", "day_of_week": 2, "time": "19:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Алена", "day_of_week": 2, "time": "20:10", "max_participants": 28},
        {"name": "Силовая", "trainer": "Алена", "day_of_week": 4, "time": "19:10", "max_participants": 28},
        # Пилатес — тренер Анна
        {"name": "Пилатес", "trainer": "Анна", "day_of_week": 0, "time": "09:30", "max_participants": 28},
        {"name": "Пилатес", "trainer": "Анна", "day_of_week": 2, "time": "09:30", "max_participants": 28},
        {"name": "Пилатес", "trainer": "Анна", "day_of_week": 4, "time": "09:30", "max_participants": 28},
        # Барре — тренер Анна
        {"name": "Барре", "trainer": "Анна", "day_of_week": 1, "time": "08:30", "max_participants": 28},
        {"name": "Барре", "trainer": "Анна", "day_of_week": 3, "time": "08:30", "max_participants": 28},
        {"name": "Барре", "trainer": "Анна", "day_of_week": 5, "time": "10:00", "max_participants": 28},
    ]

    async with async_session() as session:
        # Проверяем, есть ли уже тренировки
        result = await session.execute(
            select(func.count(Training.id)).where(Training.training_type == 'studio')
        )
        count = result.scalar()
        if count and count >= 19:
            return  # Уже заполнено

        for item in schedule:
            # Проверяем существование конкретной записи
            exists = await session.execute(
                select(Training).where(
                    Training.name == item["name"],
                    Training.trainer == item["trainer"],
                    Training.day_of_week == item["day_of_week"],
                    Training.time == item["time"],
                    Training.training_type == 'studio'
                )
            )
            if exists.scalar_one_or_none() is None:
                training = Training(
                    name=item["name"],
                    description=f'{item["name"]} — тренер {item["trainer"]}',
                    trainer=item["trainer"],
                    day_of_week=item["day_of_week"],
                    time=item["time"],
                    duration=60,
                    max_participants=item["max_participants"],
                    training_type='studio'
                )
                session.add(training)

        await session.commit()


async def get_trainings_by_filter(name: str, trainer: str = None, day_of_week: int = None):
    """Поиск тренировок по фильтру"""
    async with async_session() as session:
        query = select(Training).where(
            Training.name.startswith(name),
            Training.training_type == 'studio'
        )
        if trainer:
            query = query.where(Training.trainer == trainer)
        if day_of_week is not None:
            query = query.where(Training.day_of_week == day_of_week)
        query = query.order_by(Training.time)
        result = await session.execute(query)
        return result.scalars().all()


async def get_training_by_id(training_id: int):
    """Получить тренировку по ID"""
    async with async_session() as session:
        result = await session.execute(
            select(Training).where(Training.id == training_id)
        )
        return result.scalar_one_or_none()


async def get_bookings_count(training_id: int, booking_date: datetime):
    """Сколько записей на конкретную дату"""
    async with async_session() as session:
        # Сравниваем по дате (без учёта времени)
        date_start = booking_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        result = await session.execute(
            select(func.count(Booking.id)).where(
                Booking.training_id == training_id,
                Booking.status == 'active',
                Booking.booking_date >= date_start,
                Booking.booking_date < date_end
            )
        )
        return result.scalar() or 0


async def check_user_booking(user_id: int, training_id: int, booking_date: datetime):
    """Проверка двойной записи"""
    async with async_session() as session:
        date_start = booking_date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        result = await session.execute(
            select(Booking).where(
                Booking.user_id == user_id,
                Booking.training_id == training_id,
                Booking.status == 'active',
                Booking.booking_date >= date_start,
                Booking.booking_date < date_end
            )
        )
        return result.scalar_one_or_none()


async def create_booking(user_id: int, training_id: int, booking_date: datetime):
    """Создать запись на тренировку"""
    async with async_session() as session:
        booking = Booking(
            user_id=user_id,
            training_id=training_id,
            booking_date=booking_date,
            status='active'
        )
        session.add(booking)
        await session.commit()
        return booking


async def get_user_active_bookings(user_id: int):
    """Все активные записи пользователя (дата >= сегодня)"""
    async with async_session() as session:
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(Booking, Training)
            .join(Training, Booking.training_id == Training.id)
            .where(
                Booking.user_id == user_id,
                Booking.status == 'active',
                Booking.booking_date >= now
            )
            .order_by(Booking.booking_date)
        )
        rows = result.all()
        return [
            {
                'booking_id': row.Booking.id,
                'training_name': row.Training.name,
                'trainer': row.Training.trainer,
                'booking_date': row.Booking.booking_date,
                'training_time': row.Training.time,
            }
            for row in rows
        ]


async def cancel_booking(booking_id: int, user_id: int):
    """Отменить запись (status='cancelled'). Возвращает данные записи или None."""
    async with async_session() as session:
        result = await session.execute(
            select(Booking, Training)
            .join(Training, Booking.training_id == Training.id)
            .where(
                Booking.id == booking_id,
                Booking.user_id == user_id,
                Booking.status == 'active'
            )
        )
        row = result.first()
        if not row:
            return None

        booking = await session.get(Booking, row.Booking.id)
        booking.status = 'cancelled'
        await session.commit()

        return {
            'booking_id': row.Booking.id,
            'training_name': row.Training.name,
            'trainer': row.Training.trainer,
            'booking_date': row.Booking.booking_date,
            'training_time': row.Training.time,
        }


async def get_today_bookings():
    """Все записи на сегодня, сгруппированные по тренировке"""
    async with async_session() as session:
        now = datetime.now()
        date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        result = await session.execute(
            select(Booking, Training, User)
            .join(Training, Booking.training_id == Training.id)
            .join(User, Booking.user_id == User.user_id)
            .where(
                Booking.status == 'active',
                Booking.booking_date >= date_start,
                Booking.booking_date < date_end
            )
            .order_by(Training.time, User.name)
        )
        rows = result.all()

        grouped = {}
        for row in rows:
            key = row.Training.id
            if key not in grouped:
                grouped[key] = {
                    'training_id': row.Training.id,
                    'training_name': row.Training.name,
                    'trainer': row.Training.trainer,
                    'time': row.Training.time,
                    'clients': []
                }
            grouped[key]['clients'].append({
                'booking_id': row.Booking.id,
                'user_id': row.User.user_id,
                'name': row.User.name,
                'username': row.User.username,
            })

        return list(grouped.values())


async def mark_visit(booking_id: int, user_id: int, training_id: int):
    """Отметить посещение: создаёт Visit, ставит booking.status='completed'"""
    async with async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking or booking.status != 'active':
            return False

        booking.status = 'completed'

        visit = Visit(
            user_id=user_id,
            training_id=training_id,
            visit_date=datetime.now()
        )
        session.add(visit)
        await session.commit()
        return True