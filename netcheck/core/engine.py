from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from typing import Any, Dict, List
from netcheck.core.models import CheckResult, CheckStatus
from netcheck.core.base_checker import BaseChecker

class CheckerWorker(QObject):
    check_started = pyqtSignal(str)
    check_completed = pyqtSignal(str, list)
    all_completed = pyqtSignal(list)
    progress = pyqtSignal(int, int)

    def __init__(self, checkers: List[BaseChecker], previous_results: Dict[str, Any] = None):
        super().__init__()
        self.checkers = checkers
        self.previous_results = previous_results or {}
        self._is_cancelled = False
        
    def cancel(self):
        self._is_cancelled = True

    @pyqtSlot()
    def run(self):
        all_results = []
        checker_statuses = {} 
        
        total = len(self.checkers)
        for i, checker in enumerate(self.checkers):
            if self._is_cancelled:
                break
                
            name = checker.name()
            self.check_started.emit(name)
            
            deps_met = True
            for dep in checker.depends_on():
                dep_status = checker_statuses.get(dep)
                if dep_status is not None and dep_status not in (CheckStatus.PASS, CheckStatus.WARNING):
                    deps_met = False
                    break
                    
            if not deps_met:
                skip_result = CheckResult(
                    name=name,
                    status=CheckStatus.SKIPPED,
                    category=None, 
                    title_key="",
                    summary_key="",
                )
                checker_statuses[name] = CheckStatus.SKIPPED
                self.check_completed.emit(name, [skip_result])
                all_results.append(skip_result)
            else:
                try:
                    results = checker.check()
                    overall_status = CheckStatus.PASS
                    for r in results:
                        if r.status in (CheckStatus.FAIL, CheckStatus.WARNING):
                            overall_status = r.status
                    checker_statuses[name] = overall_status
                    self.check_completed.emit(name, results)
                    all_results.extend(results)
                except Exception as e:
                    error_result = CheckResult(
                        name=name,
                        status=CheckStatus.FAIL,
                        category=None,
                        title_key="Error",
                        summary_key=str(e)
                    )
                    checker_statuses[name] = CheckStatus.FAIL
                    self.check_completed.emit(name, [error_result])
                    all_results.append(error_result)
                    
            self.progress.emit(i + 1, total)

        self.all_completed.emit(all_results)

class CheckerEngine(QObject):
    check_started = pyqtSignal(str)
    check_completed = pyqtSignal(str, list)
    all_completed = pyqtSignal(list)
    progress = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self._checkers: List[BaseChecker] = []
        self._thread = None
        self._worker = None

    def register_checker(self, checker: BaseChecker):
        self._checkers.append(checker)

    def clear_checkers(self):
        """Remove all registered checkers (use before re-registering)."""
        if not self.is_running:
            self._checkers.clear()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def run_all(self, previous_results: Dict[str, Any] = None):
        if self.is_running:
            return

        self._thread = QThread()
        self._worker = CheckerWorker(self._checkers, previous_results)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        
        self._worker.check_started.connect(self.check_started)
        self._worker.check_completed.connect(self.check_completed)
        self._worker.progress.connect(self.progress)
        self._worker.all_completed.connect(self._on_all_completed)
        
        self._worker.all_completed.connect(self._thread.quit)
        self._worker.all_completed.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        
        self._thread.start()

    def _on_all_completed(self, results):
        self.all_completed.emit(results)
        
    def cancel(self):
        if self.is_running and self._worker:
            self._worker.cancel()
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None
