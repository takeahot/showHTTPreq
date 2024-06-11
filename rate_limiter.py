from aiolimiter import AsyncLimiter

# Создаем один экземпляр лимитера, который будет использоваться во всем проекте
limiter = AsyncLimiter(max_rate=1, time_period=1)
