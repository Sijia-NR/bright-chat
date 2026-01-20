
import { useState, useEffect } from 'react';
import { X, Star, Calendar, Trash2 } from 'lucide-react';
import { favoriteService } from '../services/favoriteService';
import { Favorite } from '../types';

interface FavoriteModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FavoriteModal: React.FC<FavoriteModalProps> = ({ isOpen, onClose }) => {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadFavorites();
    }
  }, [isOpen]);

  const loadFavorites = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await favoriteService.getFavorites(50, 0);
      setFavorites(data.favorites);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnfavorite = async (messageId: string) => {
    try {
      await favoriteService.removeFavorite(messageId);
      // 重新加载收藏列表
      loadFavorites();
    } catch (err) {
      console.error('取消收藏失败:', err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <Star className="w-5 h-5 text-white fill-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">收藏的消息</h2>
              <p className="text-sm text-blue-100">共 {total} 条收藏</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <div className="w-12 h-12 border-4 border-blue-50 border-t-blue-600 rounded-full animate-spin"></div>
              <span className="text-sm font-medium text-gray-400">加载中...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center">
                <X className="w-8 h-8 text-red-500" />
              </div>
              <p className="text-red-500 font-medium">{error}</p>
              <button
                onClick={loadFavorites}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                重新加载
              </button>
            </div>
          ) : favorites.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center">
                <Star className="w-8 h-8 text-gray-300" />
              </div>
              <p className="text-gray-400 font-medium">还没有收藏任何消息</p>
            </div>
          ) : (
            <div className="space-y-4">
              {favorites.map((fav) => (
                <div
                  key={fav.id}
                  className="group bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-all duration-200 border border-gray-200 hover:border-gray-300"
                >
                  {/* Session title */}
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 bg-blue-100 rounded-md flex items-center justify-center">
                      <Star className="w-3.5 h-3.5 text-blue-600 fill-blue-600" />
                    </div>
                    <span className="text-xs font-medium text-gray-500">
                      {fav.session.title}
                    </span>
                  </div>

                  {/* Message content */}
                  <div className="bg-white rounded-lg p-3 mb-3 border border-gray-200">
                    <p className="text-sm text-gray-800 whitespace-pre-wrap break-words">
                      {fav.message.content}
                    </p>
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{formatDate(fav.createdAt)}</span>
                    </div>
                    <button
                      onClick={() => handleUnfavorite(fav.message.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      取消收藏
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
