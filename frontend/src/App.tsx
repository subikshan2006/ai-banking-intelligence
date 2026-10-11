import React, { useEffect, useState } from 'react';
import { Navbar } from './components/common/Navbar';
import { Sidebar } from './components/common/Sidebar';
import { SimulationBanner } from './components/common/SimulationBanner';
import { Modal } from './components/common/Modal';

import { DashboardPage } from './pages/DashboardPage';
import { AssistantPage } from './pages/AssistantPage';
import { CustomersPage } from './pages/CustomersPage';
import { FraudCenterPage } from './pages/FraudCenterPage';
import { LoanCenterPage } from './pages/LoanCenterPage';
import { WorkflowMonitorPage } from './pages/WorkflowMonitorPage';
import { ApprovalCenterPage } from './pages/ApprovalCenterPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { AuditExplorerPage } from './pages/AuditExplorerPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { LoginPage } from './pages/LoginPage';

import { api, AuthUser } from './services/api';
import { simulatorWs } from './services/websocket';
import { Notification } from './types';
import { Bell, CheckCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [user, setUser] = useState<AuthUser | null>(() => {
    api.restoreToken();
    return api.getStoredUser();
  });
  const [demoRole, setDemoRole] = useState<string>('manager');
  const [isSimulatorRunning, setIsSimulatorRunning] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotificationsModal, setShowNotificationsModal] = useState<boolean>(false);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(1);
  const [openAlertsCount, setOpenAlertsCount] = useState<number>(4);

  useEffect(() => {
    if (user) setDemoRole(user.role);
  }, [user]);

  useEffect(() => {
    // Initial fetch
    loadInitialCounts();
    loadNotifications();

    // Connect WebSocket
    simulatorWs.connect();
    const unsubscribe = simulatorWs.subscribe((event: any) => {
      if (event.type === 'STATUS_CHANGED') {
        setIsSimulatorRunning(event.is_running);
      } else if (event.type === 'SNAPSHOT') {
        setIsSimulatorRunning(event.is_running);
      } else if (event.type === 'TRANSACTION_GENERATED') {
        loadInitialCounts();
        loadNotifications();
      }
    });

    return () => {
      unsubscribe();
      simulatorWs.disconnect();
    };
  }, []);

  const loadInitialCounts = async () => {
    try {
      const summary = await api.getDashboardSummary();
      setPendingApprovalsCount(summary.metrics.pending_approvals);
      setOpenAlertsCount(summary.metrics.open_fraud_alerts);
      setIsSimulatorRunning(summary.metrics.is_simulator_running);
    } catch (_) {}
  };

  const loadNotifications = async () => {
    try {
      const res = await api.getNotifications();
      setNotifications(res);
    } catch (_) {}
  };

  const handleToggleSimulator = async () => {
    try {
      if (isSimulatorRunning) {
        await api.stopSimulator();
        setIsSimulatorRunning(false);
      } else {
        await api.startSimulator();
        setIsSimulatorRunning(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateDemoTx = async () => {
    try {
      await api.generateTransaction(false);
      loadInitialCounts();
      loadNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const handleInvestigateCustomer = (customerId: string) => {
    setActiveTab('assistant');
  };

  const handleAskAssistant = (prompt: string) => {
    setActiveTab('assistant');
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
    setDemoRole('manager');
  };

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-navy-950">
      {/* Top Simulation Warning Banner */}
      <SimulationBanner />

      {/* Main Navbar */}
      <Navbar
        user={user}
        onLogout={handleLogout}
        isSimulatorRunning={isSimulatorRunning}
        onToggleSimulator={handleToggleSimulator}
        onGenerateDemoTx={handleGenerateDemoTx}
        notifications={notifications}
        onOpenNotifications={() => setShowNotificationsModal(true)}
      />

      {/* Main Body with Sidebar + Content Area */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pendingApprovalsCount={pendingApprovalsCount}
          openAlertsCount={openAlertsCount}
        />

        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <DashboardPage
              onNavigate={setActiveTab}
              onGenerateDemoTx={handleGenerateDemoTx}
            />
          )}

          {activeTab === 'assistant' && (
            <AssistantPage demoRole={demoRole} />
          )}

          {activeTab === 'customers' && (
            <CustomersPage onInvestigateCustomer={handleInvestigateCustomer} />
          )}

          {activeTab === 'fraud' && (
            <FraudCenterPage
              onAskAssistant={handleAskAssistant}
              onRequestFreeze={(acc, cust) => setActiveTab('approvals')}
            />
          )}

          {activeTab === 'loans' && <LoanCenterPage />}

          {activeTab === 'workflow' && <WorkflowMonitorPage />}

          {activeTab === 'approvals' && (
            <ApprovalCenterPage demoRole={demoRole} />
          )}

          {activeTab === 'knowledge' && <KnowledgePage />}

          {activeTab === 'audit' && <AuditExplorerPage />}

          {activeTab === 'evaluation' && <EvaluationPage />}
        </main>
      </div>

      {/* Notifications Drawer Modal */}
      {showNotificationsModal && (
        <Modal
          isOpen={true}
          onClose={() => setShowNotificationsModal(false)}
          title="In-App System & Alert Notifications"
        >
          <div className="space-y-3 text-xs">
            {notifications.length === 0 ? (
              <p className="text-slate-500 text-center py-6">No notifications currently on record.</p>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3.5 rounded-xl border flex items-start justify-between gap-3 ${
                    n.is_read ? 'bg-slate-950/40 border-slate-800/60 text-slate-400' : 'bg-slate-900 border-slate-700 text-white'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 font-bold">
                      <span>{n.title}</span>
                      {!n.is_read && <span className="w-2 h-2 rounded-full bg-teal-400"></span>}
                    </div>
                    <p className="text-[11px] text-slate-300 leading-relaxed">{n.message}</p>
                    <span className="text-[10px] text-slate-500 block">{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                  {!n.is_read && (
                    <button
                      onClick={async () => {
                        await api.markNotificationRead(n.id);
                        loadNotifications();
                      }}
                      className="text-[10px] px-2 py-1 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded font-medium shrink-0 transition"
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

export default App;
