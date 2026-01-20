
import { useState, useEffect } from 'react';
import { Star } from 'lucide-react';
import { favoriteService } from '../services/favoriteService';

interface FavoriteButtonProps {
  messageId: string;
  isFavorited?: boolean;
  onFavoriteChange?: (isFavorited: boolean) => void;
  showLabel?: boolean;
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({
  messageId,
  isFavorited: initialFavorited = false,
  onFavoriteChange,
  showLabel = false
}) => {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const [isLoading, setIsLoading] = useState(false);

  // 同步外部状态变化
  useEffect(() => {
    setIsFavorited(initialFavorited);
  }, [initialFavorited]);

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isLoading) return;

    setIsLoading(true);
    try {
      if (isFavorited) {
        await favoriteService.removeFavorite(messageId);
        setIsFavorited(false);
        onFavoriteChange?.(false);
      } else {
        await favoriteService.addFavorite(messageId);
        setIsFavorited(true);
        onFavoriteChange?.(true);
      }
    } catch (error) {
      console.error('收藏操作失败:', error);
      // 可以在这里添加错误提示
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`
        flex items-center gap-1.5 px-2 py-1.5 rounded-lg
        transition-all duration-300
        ${isFavorited
          ? 'text-yellow-500 hover:text-yellow-600 bg-yellow-50 hover:bg-yellow-100'
          : 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
        }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        active:scale-110
      `}
      title={isFavorited ? '取消收藏' : '收藏'}
    >
      <Star
        className={`w-4 h-4 ${isFavorited ? 'fill-current' : ''}`}
      />
      {showLabel && (
        <span className="text-xs font-medium">
          {isFavorited ? '已收藏' : '收藏'}
        </span>
      )}
    </button>
  );
};
