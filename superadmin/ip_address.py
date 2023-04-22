# import aiohttp
# import asyncio

# async def main():
#     async with aiohttp.ClientSession() as session:
#         pokemon_url = 'https://api64.ipify.org?format=json'
#         async with session.get(pokemon_url) as resp:
#             pokemon = await resp.json()
#         async with session.get(f"https://ipapi.co/{pokemon['ip']}/json/") as data:
#             response = await data.json()
#             location_data = {
#                 "ip": pokemon['ip'],
#                 "city": response.get("city"),
#                 "region": response.get("region"),
#                 "country": response.get("country_name")
#             }
#             return location_data

# # asyncio.run(main())
# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())