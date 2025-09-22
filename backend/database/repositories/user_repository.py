"""
User repository for user management operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from database.models.audit_log import log_user_action, log_security_event
from .base import BaseRepository, RepositoryError


class UserRepository(BaseRepository[User]):
    """Repository for User model with authentication and security features."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    @property
    def model_class(self) -> type[User]:
        return User

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = 'user',
        **kwargs
    ) -> User:
        """
        Create a new user with password hashing.

        Args:
            email: User email
            password: Plain text password
            full_name: User's full name
            role: User role (admin, user, viewer)
            **kwargs: Additional user fields

        Returns:
            Created User instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            # Check if email already exists
            existing_user = await self.find_by_email(email)
            if existing_user:
                raise RepositoryError(f"User with email {email} already exists")

            # Create user with hashed password
            user = User(
                email=email.lower().strip(),
                full_name=full_name.strip(),
                role=role,
                **kwargs
            )
            user.set_password(password)

            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

            # Log user creation
            await log_user_action(
                self.session,
                user_id=user.id,
                action='user_created',
                entity_type='user',
                entity_id=user.id,
                details={'email': email, 'role': role}
            )

            self.logger.info(f"Created user: {email} with role: {role}")
            return user

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create user {email}: {e}")
            raise RepositoryError(f"Failed to create user: {str(e)}")

    async def find_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """
        Find user by email address.

        Args:
            email: Email address to search for
            include_deleted: Whether to include soft-deleted users

        Returns:
            User instance or None if not found
        """
        try:
            query = select(User).where(User.email == email.lower().strip())

            if not include_deleted:
                query = query.where(User.deleted_at.is_(None))

            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self.logger.debug(f"Found user by email: {email}")
            else:
                self.logger.debug(f"No user found with email: {email}")

            return user

        except Exception as e:
            self.logger.error(f"Error finding user by email {email}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User instance if authentication successful, None otherwise
        """
        try:
            user = await self.find_by_email(email)

            if not user:
                await log_security_event(
                    self.session,
                    event_type='authentication_failed',
                    details={'email': email, 'reason': 'user_not_found'}
                )
                return None

            # Check if account is locked
            if user.is_locked():
                await log_security_event(
                    self.session,
                    user_id=user.id,
                    event_type='authentication_failed',
                    details={'email': email, 'reason': 'account_locked'}
                )
                return None

            # Check if account is active
            if not user.is_active:
                await log_security_event(
                    self.session,
                    user_id=user.id,
                    event_type='authentication_failed',
                    details={'email': email, 'reason': 'account_inactive'}
                )
                return None

            # Verify password
            if not user.check_password(password):
                user.increment_login_attempts()
                await self.session.flush()

                await log_security_event(
                    self.session,
                    user_id=user.id,
                    event_type='authentication_failed',
                    details={
                        'email': email,
                        'reason': 'invalid_password',
                        'login_attempts': user.login_attempts
                    }
                )
                return None

            # Successful authentication
            user.reset_login_attempts()
            await self.session.flush()

            await log_security_event(
                self.session,
                user_id=user.id,
                event_type='authentication_success',
                details={'email': email}
            )

            self.logger.info(f"User authenticated successfully: {email}")
            return user

        except Exception as e:
            self.logger.error(f"Authentication error for {email}: {e}")
            raise RepositoryError(f"Authentication error: {str(e)}")

    async def update_password(self, user_id: str, new_password: str) -> bool:
        """
        Update user password.

        Args:
            user_id: User ID
            new_password: New plain text password

        Returns:
            True if password updated successfully

        Raises:
            RepositoryError: If update fails
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None

            await self.session.flush()

            await log_security_event(
                self.session,
                user_id=user.id,
                event_type='password_changed',
                details={'email': user.email}
            )

            self.logger.info(f"Password updated for user: {user.email}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update password for user {user_id}: {e}")
            raise RepositoryError(f"Failed to update password: {str(e)}")

    async def set_password_reset_token(self, email: str, token: str, expires: datetime) -> bool:
        """
        Set password reset token for user.

        Args:
            email: User email
            token: Reset token
            expires: Token expiration datetime

        Returns:
            True if token set successfully
        """
        try:
            user = await self.find_by_email(email)
            if not user:
                return False

            user.password_reset_token = token
            user.password_reset_expires = expires

            await self.session.flush()

            await log_security_event(
                self.session,
                user_id=user.id,
                event_type='password_reset_requested',
                details={'email': email}
            )

            self.logger.info(f"Password reset token set for user: {email}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to set reset token for {email}: {e}")
            raise RepositoryError(f"Failed to set reset token: {str(e)}")

    async def verify_reset_token(self, token: str) -> Optional[User]:
        """
        Verify password reset token and return user.

        Args:
            token: Reset token to verify

        Returns:
            User instance if token is valid, None otherwise
        """
        try:
            query = select(User).where(
                and_(
                    User.password_reset_token == token,
                    User.password_reset_expires > datetime.utcnow(),
                    User.deleted_at.is_(None)
                )
            )

            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self.logger.debug(f"Valid reset token for user: {user.email}")
            else:
                self.logger.debug(f"Invalid or expired reset token: {token}")

            return user

        except Exception as e:
            self.logger.error(f"Error verifying reset token: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated successfully
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            user.last_login_at = datetime.utcnow()
            await self.session.flush()

            self.logger.debug(f"Updated last login for user: {user.email}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise RepositoryError(f"Failed to update last login: {str(e)}")

    async def get_active_users(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = 'created_at',
        order_desc: bool = True
    ) -> List[User]:
        """
        Get all active users.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order

        Returns:
            List of active User instances
        """
        try:
            query = select(User).where(
                and_(
                    User.is_active == True,
                    User.deleted_at.is_(None)
                )
            )

            if order_by and hasattr(User, order_by):
                order_column = getattr(User, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column)

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            users = result.scalars().all()

            self.logger.debug(f"Retrieved {len(users)} active users")
            return list(users)

        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def search_users(
        self,
        search_term: str,
        include_inactive: bool = False,
        limit: Optional[int] = None
    ) -> List[User]:
        """
        Search users by email or full name.

        Args:
            search_term: Term to search for
            include_inactive: Whether to include inactive users
            limit: Maximum number of results

        Returns:
            List of matching User instances
        """
        try:
            search_pattern = f"%{search_term.lower()}%"

            query = select(User).where(
                and_(
                    or_(
                        User.email.like(search_pattern),
                        User.full_name.like(search_pattern)
                    ),
                    User.deleted_at.is_(None)
                )
            )

            if not include_inactive:
                query = query.where(User.is_active == True)

            if limit is not None:
                query = query.limit(limit)

            query = query.order_by(User.full_name)

            result = await self.session.execute(query)
            users = result.scalars().all()

            self.logger.debug(f"Search for '{search_term}' found {len(users)} users")
            return list(users)

        except Exception as e:
            self.logger.error(f"Error searching users: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_users_by_role(self, role: str) -> List[User]:
        """
        Get all users with specific role.

        Args:
            role: User role to filter by

        Returns:
            List of User instances with the specified role
        """
        try:
            query = select(User).where(
                and_(
                    User.role == role,
                    User.deleted_at.is_(None)
                )
            ).order_by(User.full_name)

            result = await self.session.execute(query)
            users = result.scalars().all()

            self.logger.debug(f"Found {len(users)} users with role: {role}")
            return list(users)

        except Exception as e:
            self.logger.error(f"Error getting users by role {role}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: Dictionary of preferences to update

        Returns:
            True if updated successfully
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return False

            # Update preferences while preserving existing ones
            if user.preferences is None:
                user.preferences = {}

            for key, value in preferences.items():
                user.update_preference(key, value)

            await self.session.flush()

            await log_user_action(
                self.session,
                user_id=user.id,
                action='preferences_updated',
                entity_type='user',
                entity_id=user.id,
                details={'updated_keys': list(preferences.keys())}
            )

            self.logger.info(f"Updated preferences for user: {user.email}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update preferences for user {user_id}: {e}")
            raise RepositoryError(f"Failed to update preferences: {str(e)}")

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        try:
            # Total users
            total_query = select(func.count()).select_from(User).where(
                User.deleted_at.is_(None)
            )
            total_result = await self.session.execute(total_query)
            total_users = total_result.scalar()

            # Active users
            active_query = select(func.count()).select_from(User).where(
                and_(
                    User.is_active == True,
                    User.deleted_at.is_(None)
                )
            )
            active_result = await self.session.execute(active_query)
            active_users = active_result.scalar()

            # Users by role
            role_query = select(User.role, func.count()).select_from(User).where(
                User.deleted_at.is_(None)
            ).group_by(User.role)
            role_result = await self.session.execute(role_query)
            users_by_role = dict(role_result.all())

            # Recent users (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = select(func.count()).select_from(User).where(
                and_(
                    User.created_at >= thirty_days_ago,
                    User.deleted_at.is_(None)
                )
            )
            recent_result = await self.session.execute(recent_query)
            recent_users = recent_result.scalar()

            statistics = {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'users_by_role': users_by_role,
                'recent_users': recent_users
            }

            self.logger.debug("Generated user statistics")
            return statistics

        except Exception as e:
            self.logger.error(f"Error generating user statistics: {e}")
            raise RepositoryError(f"Database error: {str(e)}")