import React, { createContext, useContext, useState, useCallback } from 'react';
import Toast, { ToastType } from '../components/common/Toast';
import ConfirmDialog from '../components/common/ConfirmDialog';
import InputDialog from '../components/common/InputDialog';

interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
}

interface InputOptions {
  title: string;
  placeholder?: string;
  defaultValue?: string;
  multiline?: boolean;
  rows?: number;
  confirmText?: string;
  cancelText?: string;
}

interface ModalContextValue {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  showConfirm: (options: ConfirmOptions) => Promise<boolean>;
  showInput: (options: InputOptions) => Promise<string | null>;
}

const ModalContext = createContext<ModalContextValue | undefined>(undefined);

export const useModal = () => {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModal must be used within ModalProvider');
  }
  return context;
};

interface ModalProviderProps {
  children: React.ReactNode;
}

export const ModalProvider: React.FC<ModalProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmOptions & { resolve: (value: boolean) => void } | null>(null);
  const [inputDialog, setInputDialog] = useState<InputOptions & { resolve: (value: string | null) => void } | null>(null);

  const showToast = useCallback((message: string, type: ToastType = 'info', duration: number = 3000) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration + 300); // 加上动画时间
  }, []);

  const showConfirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise(resolve => {
      setConfirmDialog({ ...options, resolve });
    });
  }, []);

  const showInput = useCallback((options: InputOptions): Promise<string | null> => {
    return new Promise(resolve => {
      setInputDialog({ ...options, resolve });
    });
  }, []);

  const handleConfirmClose = (confirmed: boolean) => {
    if (confirmDialog) {
      confirmDialog.resolve(confirmed);
      setConfirmDialog(null);
    }
  };

  const handleInputClose = (value: string | null) => {
    if (inputDialog) {
      inputDialog.resolve(value);
      setInputDialog(null);
    }
  };

  return (
    <ModalContext.Provider value={{ showToast, showConfirm, showInput }}>
      {children}

      {/* Toast 通知 */}
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
        />
      ))}

      {/* 确认对话框 */}
      {confirmDialog && (
        <ConfirmDialog
          isOpen={true}
          title={confirmDialog.title}
          message={confirmDialog.message}
          confirmText={confirmDialog.confirmText}
          cancelText={confirmDialog.cancelText}
          type={confirmDialog.type}
          onConfirm={() => handleConfirmClose(true)}
          onCancel={() => handleConfirmClose(false)}
        />
      )}

      {/* 输入对话框 */}
      {inputDialog && (
        <InputDialog
          isOpen={true}
          title={inputDialog.title}
          placeholder={inputDialog.placeholder}
          defaultValue={inputDialog.defaultValue}
          multiline={inputDialog.multiline}
          rows={inputDialog.rows}
          confirmText={inputDialog.confirmText}
          cancelText={inputDialog.cancelText}
          onConfirm={handleInputClose}
          onCancel={() => handleInputClose(null)}
        />
      )}
    </ModalContext.Provider>
  );
};
