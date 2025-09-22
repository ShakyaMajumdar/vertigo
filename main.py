from dataclasses import dataclass
import sys
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.InputStateGlobal import inputState
from panda3d.bullet import BulletPlaneShape, BulletRigidBodyNode, BulletWorld, BulletCapsuleShape, BulletCharacterControllerNode, ZUp
from panda3d.core import Vec3, CardMaker, TextureStage, DirectionalLight, AmbientLight, WindowProperties


@dataclass
class GameSettings:
    speed: float = 20
    gravity: float = 9.81
    jump_height: float = 0.7
    jump_speed: float = 10
    mouse_sensitivity = 0.1


class GameScene:
    def __init__(self, world, render, loader, camera, win, game_settings: GameSettings):
        self.render = render
        self.loader = loader
        self.world = world
        self.camera = camera
        self.win = win
        self.game_settings = game_settings

        self.world.setGravity(Vec3(0, 0, -self.game_settings.gravity))
        self.setup_window()
        self.setup_light()
        self.setup_ground()
        self.setup_player()
        self.setup_controls()

    def setup_window(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)
    
    def setup_light(self):
        dlight = DirectionalLight('dlight')
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

    def setup_ground(self):
        self.ground_n = BulletRigidBodyNode('Ground')
        self.ground_n.addShape(BulletPlaneShape(Vec3(0, 0, 1), 1))
        self.ground_np = self.render.attachNewNode(self.ground_n)
        self.ground_np.setPos(0, 0, -2)
        ground_cm = CardMaker('ground_card')
        ground_cm.setFrame(-50, 50, -50, 50) 
        ground_vis = self.ground_np.attachNewNode(ground_cm.generate())
        ground_vis.setHpr(0, -90, 0)   
        ground_vis.setPos(0, 0, 1) 
        ground_tex = self.loader.loadTexture("maps/grid.rgb")  
        ground_vis.setTexture(ground_tex)
        ground_vis.setTexScale(TextureStage.getDefault(), 5, 5)
        self.world.attachRigidBody(self.ground_n)
    
    def setup_player(self):
        self.player_n = BulletCharacterControllerNode(BulletCapsuleShape(0.4, 1.0, ZUp), 0.4, "Player")
        self.player_np = self.render.attachNewNode(self.player_n)
        self.player_np.setPos(0, 0, 2)
        self.player_n.setGravity(self.game_settings.gravity)
        self.player_n.setMaxJumpHeight(self.game_settings.jump_height)
        self.player_n.setJumpSpeed(self.game_settings.jump_speed)
        self.world.attachCharacter(self.player_n)

        self.camera.reparentTo(self.player_np)
        self.camera.setPos(0, 0, 1.5)  

        self.pitch = 0  
    
    def setup_controls(self):
        inputState.watchWithModifiers("forward", "w")
        inputState.watchWithModifiers("backward", "s")
        inputState.watchWithModifiers("left", "a")
        inputState.watchWithModifiers("right", "d")
        inputState.watchWithModifiers("jump", "space")

    def process_mouse(self):
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()

        self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
        dx = (x - self.win.getXSize() // 2) * self.game_settings.mouse_sensitivity
        dy = (y - self.win.getYSize() // 2) * self.game_settings.mouse_sensitivity

        self.player_np.setH(self.player_np.getH() - dx)

        self.pitch = max(-90, min(90, self.pitch - dy))
        self.camera.setP(self.pitch)

    def process_movement(self, dt):
        direction = Vec3(0, 0, 0)
        if inputState.isSet("forward"):
            direction.y += 1
        if inputState.isSet("backward"):
            direction.y -= 1
        if inputState.isSet("left"):
            direction.x -= 1
        if inputState.isSet("right"):
            direction.x += 1

        direction.normalize()

        quat = self.player_np.getQuat(self.render)
        dir_world = quat.xform(direction)
        dir_world.setZ(0)
        dir_world.normalize()

        self.player_n.setLinearMovement(dir_world * self.game_settings.speed, False)

        if inputState.isSet("jump"):
            if self.player_n.isOnGround():
                self.player_n.doJump()
        

    def update(self, task):
        dt = globalClock.getDt()
        self.process_mouse()
        self.process_movement(dt)
        self.world.doPhysics(dt)
        return task.cont


class App(ShowBase):
    def __init__(self):
        super().__init__()
        self.accept("escape", self.exit_app)
        self.disableMouse()
        game_scene = GameScene(BulletWorld(), self.render, self.loader, self.camera, self.win, GameSettings())
        self.taskMgr.add(game_scene.update, 'update')
    
    def exit_app(self):
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.run()
