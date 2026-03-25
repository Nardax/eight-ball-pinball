"""Custom Game mode override adding ``players`` property for test compatibility.

MPF 0.57.4's built-in Game class exposes ``player_list`` but tests access
``machine.game.players``. This thin subclass adds the alias.
"""

from mpf.modes.game.code.game import Game as MpfGame


class Game(MpfGame):
    """Eight Ball custom Game mode — adds ``players`` alias for ``player_list``."""

    @property
    def players(self):
        """Return the list of all Player objects (alias for player_list)."""
        return self.player_list
