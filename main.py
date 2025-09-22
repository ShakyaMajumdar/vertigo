from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.bullet import BulletPlaneShape, BulletRigidBodyNode, BulletWorld, BulletBoxShape
from panda3d.core import Vec3, CardMaker, TextureStage, DirectionalLight, AmbientLight

class GameScene:
    def __init__(self, world, render, loader):
        self.render = render
        self.loader = loader
        self.world = world

        dlight = DirectionalLight('dlight')
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        self.world.setGravity(Vec3(0, 0, -9.81))

        ground_n = BulletRigidBodyNode('Ground')
        ground_n.addShape(BulletPlaneShape(Vec3(0, 0, 1), 1))
        ground_np = self.render.attachNewNode(ground_n)
        ground_np.setPos(0, 0, -2)
        ground_cm = CardMaker('ground_card')
        ground_cm.setFrame(-50, 50, -50, 50) 
        ground_vis = ground_np.attachNewNode(ground_cm.generate())
        ground_vis.setHpr(0, -90, 0)   
        ground_vis.setPos(0, 0, 1) 
        ground_tex = self.loader.loadTexture("maps/grid.rgb")  
        ground_vis.setTexture(ground_tex)
        ground_vis.setTexScale(TextureStage.getDefault(), 10, 10)
        self.world.attachRigidBody(ground_n)

        box_n = BulletRigidBodyNode('Box')
        box_n.setMass(1.0)
        box_n.addShape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))
        box_np = render.attachNewNode(box_n)
        box_np.setPos(0, 0, 2)
        world.attachRigidBody(box_n)
        box_model = self.loader.loadModel('models/box.egg')
        box_model.flattenLight()
        box_model.reparentTo(box_np)
    
    def update(self, task):
        dt = globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont


class App(ShowBase):
    def __init__(self):
        super().__init__()
        self.cam.setPos(0, -10, 0)
        self.cam.lookAt(0, 0, 0)
        game_scene = GameScene(BulletWorld(), self.render, self.loader)
        self.taskMgr.add(game_scene.update, 'update')


if __name__ == "__main__":
    app = App()
    app.run()
