
import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning';
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  confirmText = '确认',
  cancelText = '取消',
  type = 'danger'
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-sm rounded-[24px] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
        <div className="p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
              type === 'danger' ? 'bg-red-50 text-red-500' : 'bg-amber-50 text-amber-500'
            }`}>
              <AlertCircle size={24} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-500 mt-1">{message}</p>
            </div>
          </div>
          
          <div className="flex gap-3 mt-6">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2.5 bg-gray-50 hover:bg-gray-100 text-gray-600 rounded-xl text-sm font-bold transition-colors"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 px-4 py-2.5 text-white rounded-xl text-sm font-bold transition-all active:scale-95 shadow-lg ${
                type === 'danger' ? 'bg-red-600 hover:bg-red-700 shadow-red-100' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-100'
              }`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
