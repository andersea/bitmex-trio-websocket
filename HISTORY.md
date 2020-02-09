# History

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
