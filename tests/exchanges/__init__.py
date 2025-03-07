#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import os
import mock
import pytest
import pytest_asyncio

import octobot_commons.constants as commons_constants
from octobot_backtesting.backtesting import Backtesting
from octobot_backtesting.constants import CONFIG_BACKTESTING
import octobot_backtesting.time as backtesting_time
from octobot_commons.asyncio_tools import wait_asyncio_next_cycle
from octobot_commons.enums import TimeFrames

from octobot_commons.tests.test_config import load_test_config
from octobot_trading.api.exchange import create_exchange_builder, cancel_ccxt_throttle_task
from octobot_trading.exchanges.exchange_manager import ExchangeManager
from octobot_trading.exchanges.traders.trader_simulator import TraderSimulator
import octobot_trading.personal_data as personal_data

pytestmark = pytest.mark.asyncio

TESTS_FOLDER = "tests"
TESTS_STATIC_FOLDER = os.path.join(TESTS_FOLDER, "static")
DEFAULT_EXCHANGE_NAME = "binance"


@pytest_asyncio.fixture
async def exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = True
    exchange_manager_instance.is_simulated = False
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def simulated_exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = True
    exchange_manager_instance.is_simulated = True
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def margin_exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = False
    exchange_manager_instance.is_margin = True
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def margin_simulated_exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = False
    exchange_manager_instance.is_simulated = True
    exchange_manager_instance.is_margin = True
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def future_exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = False
    exchange_manager_instance.is_future = True
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def future_simulated_exchange_manager():
    exchange_manager_instance = ExchangeManager(load_test_config(), DEFAULT_EXCHANGE_NAME)
    exchange_manager_instance.is_spot_only = False
    exchange_manager_instance.is_simulated = True
    exchange_manager_instance.is_future = True
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    cancel_ccxt_throttle_task()
    await exchange_manager_instance.stop()
    # let updaters gracefully shutdown
    await wait_asyncio_next_cycle()


@pytest_asyncio.fixture
async def exchange_builder(request):
    config = None
    exchange_name = DEFAULT_EXCHANGE_NAME
    if hasattr(request, "param"):
        config, exchange_name = request.param

    exchange_builder_instance = create_exchange_builder(config if config is not None else load_test_config(),
                                                        exchange_name).is_simulated().is_rest_only()
    yield exchange_builder_instance
    await exchange_builder_instance.exchange_manager.stop()


# SIMULATED / BACKTESTING
DEFAULT_BACKTESTING_SYMBOL = "BTC/USDT"
DEFAULT_BACKTESTING_SPLIT_SYMBOL = "BTC", "USDT"
DEFAULT_BACKTESTING_CURRENCY = "BTC"
DEFAULT_BACKTESTING_MARKET = "USDT"
DEFAULT_BACKTESTING_TF = TimeFrames.ONE_HOUR


@pytest_asyncio.fixture
async def backtesting_config(request):
    config = load_test_config()
    config[CONFIG_BACKTESTING] = {}
    config[CONFIG_BACKTESTING][commons_constants.CONFIG_ENABLED_OPTION] = True
    if hasattr(request, "param"):
        ref_market = request.param
        config[commons_constants.CONFIG_TRADING][commons_constants.CONFIG_TRADER_REFERENCE_MARKET] = ref_market
    return config


@pytest_asyncio.fixture
async def fake_backtesting(backtesting_config):
    return Backtesting(config=backtesting_config,
                       exchange_ids=[],
                       matrix_id="",
                       backtesting_files=[])


@pytest_asyncio.fixture
async def backtesting_exchange_manager(request, backtesting_config, fake_backtesting):
    config = None
    exchange_name = DEFAULT_EXCHANGE_NAME
    is_spot = True
    is_margin = False
    is_future = False
    if hasattr(request, "param"):
        config, exchange_name, is_spot, is_margin, is_future = request.param

    if config is None:
        config = backtesting_config
    exchange_manager_instance = ExchangeManager(config, exchange_name)
    exchange_manager_instance.is_backtesting = True
    exchange_manager_instance.is_spot_only = is_spot
    exchange_manager_instance.is_margin = is_margin
    exchange_manager_instance.is_future = is_future
    exchange_manager_instance.backtesting = fake_backtesting
    exchange_manager_instance.backtesting.time_manager = backtesting_time.TimeManager(config)
    await exchange_manager_instance.initialize()
    yield exchange_manager_instance
    await exchange_manager_instance.stop()


@pytest_asyncio.fixture
async def simulated_trader(simulated_exchange_manager):
    config = load_test_config()
    trader_instance = TraderSimulator(config, simulated_exchange_manager)
    await trader_instance.initialize()
    return config, simulated_exchange_manager, trader_instance


@pytest_asyncio.fixture
async def backtesting_trader(backtesting_config, backtesting_exchange_manager):
    trader_instance = TraderSimulator(backtesting_config, backtesting_exchange_manager)
    await trader_instance.initialize()
    return backtesting_config, backtesting_exchange_manager, trader_instance


def storage_mock():
    return mock.Mock(
        portfolio_storage=mock.Mock(
            get_db=mock.Mock(
                return_value=mock.Mock(
                    all=mock.AsyncMock(return_value=[])
                )
            ),
            save_historical_portfolio_value=mock.AsyncMock(),
        ),
        stop=mock.AsyncMock(),
    )


@pytest_asyncio.fixture
async def backtesting_trader_with_historical_pf_value_manager(backtesting_trader):
    backtesting_config, backtesting_exchange_manager, trader_instance = backtesting_trader
    backtesting_exchange_manager.storage_manager = storage_mock()
    historical_portfolio_value_manager_inst = personal_data.HistoricalPortfolioValueManager(
        backtesting_exchange_manager.exchange_personal_data.portfolio_manager
    )
    backtesting_exchange_manager.exchange_personal_data.portfolio_manager.historical_portfolio_value_manager = \
        historical_portfolio_value_manager_inst
    await historical_portfolio_value_manager_inst.initialize()
    backtesting_exchange_manager.exchange_personal_data.portfolio_manager.handle_profitability_recalculation(True)
    return backtesting_config, backtesting_exchange_manager, trader_instance


@pytest_asyncio.fixture
async def margin_backtesting_trader(backtesting_config, backtesting_exchange_manager):
    trader_instance = TraderSimulator(backtesting_config, backtesting_exchange_manager)
    await trader_instance.initialize()
    return backtesting_config, backtesting_exchange_manager, trader_instance


@pytest_asyncio.fixture
async def future_backtesting_trader(backtesting_config, backtesting_exchange_manager):
    trader_instance = TraderSimulator(backtesting_config, backtesting_exchange_manager)
    await trader_instance.initialize()
    return backtesting_config, backtesting_exchange_manager, trader_instance
