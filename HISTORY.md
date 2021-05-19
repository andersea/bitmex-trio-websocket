# History

## 0.14.1 (2021-05-19)

* Log websocket closure on errors.

## 0.14.0 (2021-05-13)

Remote closure behaviour changed again. Closure will now result in a ConnectionClosed error being raised into the pipeline.
Listeners will simply be closed.

## 0.13.2 (2021-05-06)

* Revert 0.13.1 error handling to 0.13.0. It is most likely preferable that all listeners are notified of websocket closure.
* Update slurry-websocket.

## 0.13.1 (2021-05-05)

* Raising on all listeners seems a bit noisy. Now raises once from the context manager, if close code != 1000.
* Update dependencies.

## 0.13.0 (2021-05-03)

New behaviour: If the websocket is closed remotely, bitmex-trio-websocket will now raise trio-websocket.ConnectionClosed,
and include the underlying reason for the closure, on all open listeners. Previously, listener generator functions would
simply end silently, and you would have to either assume that the websocket was remotely closed, or peek into the private
_websocket attribute to check the underlying websocket state.

## 0.12.2 (2021-04-29)

* Check if the websocket is still open, before attempting to unsubscribe from tables. No sense talking to a dead phone line.

## 0.12.1 (2021-02-23)

* Upgrade slurry-websocket for better closure handling.

## 0.12.0 (2021-02-05)

The websocket is now forced to connect when the open_bitmex_websocket context is entered. Previously, the websocket
would lazily wait for a subscription to be added, before it would connect. This creates problems because the user will
probably want to know if the connection has succeeded, before any subscriptions are attempted. Especially so, if those
subscriptions require an authenticated connection.

* Upgrade slurry-websocket
* Add check for websocket status, before adding a subscription. There was a check previously, but it would always succeed.
* Slightly more verbose logging on startup and shutdown.

## 0.11.2 (2020-12-27)

* Upgrade slurry

## 0.11.1 (2020-12-25)

* Upgrade slurry

## 0.11.0 (2020-12-16)

* Will now raise BitMEXWebsocketApiError on any error message. This is a breaking change. Up to now, all errors were simply discarded. No error handling is attempted. Any error will cause the connection to be terminated and will raise BitMEXWebsocketApiError.

## 0.10.5 (2020-12-13)

* Upgrade slurry

## 0.10.4 (2020-12-04)

* Update to latest slurry

## 0.10.3 (2020-11-28)

* Update dependencies
* Fix broken tests

## 0.10.1 (2020-11-02)

* Support multisymbol subscriptions per listener

## 0.9.0 (2020-09-05)

* Bitmex trio websocket is now based on the [Slurry](https://slurry.readthedocs.io/en/latest/) streaming data processing microframework.

## 0.8.1 (2020-07-02)

* Documentation: Remove link to missing docs. See the readme for documentation.

## 0.8.0 (2020-04-11)

* Better propagation of connection closure. Before, if the websocket was closed by the remote server for any reason, bitmex_trio_websocket would simply output a log message and take no further action. This is obviously a problem, because the client application now has no way to tell that the connection is closed, other than contrived means, like polling the underlying trio_websocket object periodically. Now, connection closure results in the following:
    * All listen channels will be closed. No reason is given for the closure.
    * Attemts to open new listen channels will cause trio.ClosedResourceError to be raised.
    * It is assumed that closing of listen channels causes the websocket context to exit in the client application. At context exit, the exception that caused the underlying trio_websocket to close is reraised as a notification to the client application.

## 0.7.1 (2020-03-04)

* Fix: RuntimeError: dictionary changed size during iteration, when listeners added while simultaneously sending a message.

## 0.7.0 (2020-03-01)

* Add support for custom user defined table keys.

## 0.6.5 (2020-02-16)

* Fix: Multiple subscriptions to the same channel was not handled properly, resulting in log warnings.
* Fix: Use pendulum to parse RFC 3339 timestamps

## 0.6.1 (2020-02-14)

* Warning! Thorough refactoring resulting in major api changes. `BitMEXWebsocket` is now created using the `open_bitmex_websocket` function, which is a standalone async context manager. It returns a BitMEXWebsocket.
* Deletions are now broadcasted to listeners.

## 0.5.2 (2020-02-09)

* Fix: Uses aclosing from async_generator library for context management of all async generators to ensure safe garbage collection. Always ensure you context manage async generators. They *will* shoot you in the foot otherwise!
* Fix: Handle response message from dead mans switch.

## 0.5.0 (2020-02-09)

* Added optional dead mans switch. See: https://www.bitmex.com/app/wsAPI#Dead-Mans-Switch-Auto-Cancel

## 0.4.4 (2020-02-08)

* Fixed table storage for insert-only keyless tables, like tradeBin. Uses attributes from partial message instead of the keys list.

## 0.4.2 (2020-02-05)

* Relaxed python dependency to 3.6

## 0.4.1 (2020-02-05)

* Checks network argument to BitMEXWebsocket init method is valid.
* storage.insert() method allows storage to be patched externally.

## 0.4.0 (2020-02-03)

* Big refactoring.
* Handles subscriptions individually per channel.
* Data storage uses sorted containers for search efficiency.

## 0.2.5 (2019-11-25)

* Documentation fixes.

## 0.2.4 (2019-11-24)

* Added documentation.

## 0.2.1 (2019-11-24)

* First release on PyPI.
