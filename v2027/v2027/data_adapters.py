
from abc import ABC, abstractmethod

class MarketDataProvider(ABC):
    @abstractmethod
    def history(self,ticker,start=None,end=None): ...
    @abstractmethod
    def quote(self,ticker): ...

class FundamentalDataProvider(ABC):
    @abstractmethod
    def point_in_time_financials(self,tickers,start=None,end=None): ...

class AnnouncementProvider(ABC):
    @abstractmethod
    def announcements(self,ticker,start=None,end=None): ...

class MacroDataProvider(ABC):
    @abstractmethod
    def series(self,name,start=None,end=None): ...

class NewsProvider(ABC):
    @abstractmethod
    def company_news(self,ticker,start=None,end=None): ...

# These interfaces allow Yahoo/prototype sources to be replaced later with
# licensed ASX/financial providers without rewriting the analytical engines.
