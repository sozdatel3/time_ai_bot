from dataclasses import dataclass
from typing import Optional

import aiohttp


@dataclass
class LocationInfo:
    """Информация о локации"""

    lat: float
    lng: float
    city: str
    country: str
    full_address: str


class GeocodingService:
    """Сервис для работы с геолокацией"""

    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org/reverse"
        # self.search_url = "https://nominatim.openstreetmap.org/search"
        self.search_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {"User-Agent": "AstroBot/1.0"}

    async def get_location_info(
        self, lat: float, lng: float
    ) -> Optional[LocationInfo]:
        """Получить информацию о локации по координатам"""
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "accept-language": "ru",
            "zoom": 10,  # Уровень детализации (10 = город)
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.nominatim_url, params=params, headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Извлекаем информацию о городе
                        address = data.get("address", {})

                        # Пытаемся найти город в разных полях
                        city = (
                            address.get("city")
                            or address.get("town")
                            or address.get("village")
                            or address.get("municipality")
                            or address.get("state_district")
                            or address.get("state", "")
                        )

                        country = address.get("country", "")
                        full_address = data.get("display_name", "")

                        return LocationInfo(
                            lat=lat,
                            lng=lng,
                            city=city,
                            country=country,
                            full_address=full_address,
                        )
                    else:
                        print(f"Geocoding error: {response.status}")
                        return None

        except Exception as e:
            print(f"Geocoding exception: {e}")
            return None

    async def get_location_from_query(
        self, query: str
    ) -> Optional[LocationInfo]:
        """Получить информацию о локации по текстовому запросу"""
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "accept-language": "ru",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.search_url, params=params, headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            return None

                        place = data[0]
                        address = place.get("address", {})

                        city = (
                            address.get("city")
                            or address.get("town")
                            or address.get("village")
                            or address.get("municipality")
                            or address.get("state_district")
                            or address.get("state", "")
                        )

                        country = address.get("country", "")
                        full_address = place.get("display_name", "")

                        return LocationInfo(
                            lat=float(place["lat"]),
                            lng=float(place["lon"]),
                            city=city,
                            country=country,
                            full_address=full_address,
                        )
                    else:
                        print(f"Geocoding search error: {response.status}")
                        return None

        except Exception as e:
            print(f"Geocoding search exception: {e}")
            return None

    def format_location_string(self, location_info: LocationInfo) -> str:
        """Форматировать строку с локацией"""
        if location_info.city and location_info.country:
            return f"{location_info.city}, {location_info.country}"
        elif location_info.city:
            return location_info.city
        elif location_info.country:
            return location_info.country
        else:
            return (
                f"Координаты: {location_info.lat:.4f}, {location_info.lng:.4f}"
            )


# async def get_location_from_query(
#         self, query: str
#     ) -> Optional[LocationInfo]:
#         """Получить информацию о локации по текстовому запросу"""
#         params = {
#             "q": query,
#             "format": "json",
#             "limit": 1,
#             "addressdetails": 1,
#             "accept-language": "ru",
#         }

#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(
#                     self.search_url, params=params, headers=self.headers
#                 ) as response:
#                     if response.status == 200:
#                         data = await response.json()
#                         if not data:
#                             return None

#                         place = data[0]
#                         address = place.get("address", {})

#                         city = (
#                             address.get("city")
#                             or address.get("town")
#                             or address.get("village")
#                             or address.get("municipality")
#                             or address.get("state_district")
#                             or address.get("state", "")
#                         )

#                         country = address.get("country", "")
#                         full_address = place.get("display_name", "")

#                         return LocationInfo(
#                             lat=float(place["lat"]),
#                             lng=float(place["lon"]),
#                             city=city,
#                             country=country,
#                             full_address=full_address,
#                         )
#                     else:
#                         print(f"Geocoding search error: {response.status}")
#                         return None

#         except Exception as e:
#             print(f"Geocoding search exception: {e}")
#             return None
