# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    'name': "Smart F",
    'author': "Duyun Ivan",
    'version': (1, 0, 0),
    'blender': (2, 78, 0),
    'location': "Editmode > F",
    'warning': "",
    'description': "Smart and fast making face",
    'wiki_url': "", 
    'tracker_url': "",
    'category': 'Mesh'}


import bmesh
import bpy
import itertools
import mathutils
import math
from bpy_extras import view3d_utils

from bpy.props import *
from math import pi, radians

           
class DialogErrorMessage(bpy.types.Operator):
    bl_idname = "object.dialog_error_message"
    bl_label = "Error!!!"
    
    def execute(self, context):
        #message = "Popup Values: %f, %d, '%s'" % (self.my_float, self.my_bool, self.my_string)        
        #self.report({'INFO'}, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
    def draw(self, context):
        layout = self.layout        
        box = layout.box()          
        box.label(text="Can not create face!!!") 
        box.label(text="Check mesh. Try to move selected vert.")    
        box.label(text="Or try to switch off checks for angle or area.")        
         
    
class SmartFMenu(bpy.types.Panel):
    bl_idname = "SmartF"      
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'    
    bl_category = "SmartF"   
    bl_context = "mesh_edit"
    bl_label = "Tools"
    
    #bl_options = {'DEFAULT_CLOSED'}
    
    enum_items = (('0','','in','PASTEDOWN',0),('1','','out','COPYDOWN',1))            
    bpy.types.Scene.normal_direction = bpy.props.EnumProperty(items = enum_items)                                   

    enum_items = (('0','','triangle','PLAY',0),('1','','quad','MESH_PLANE',1))            
    bpy.types.Scene.triangle_or_square = bpy.props.EnumProperty(items = enum_items)                 
    
    bpy.types.Scene.all_face_from_one_vert = bpy.props.BoolProperty(
      name="all_face_from_one_vert",
      description="Make all face from one vert",
      default = False )
    
    bpy.types.Scene.auto_select_next_vert = bpy.props.BoolProperty(
      name="auto_select_next_vert",
      description="Auto select next vert",
      default = True )
      
    bpy.types.Scene.check_angle = bpy.props.BoolProperty(
      name="check_angle",
      description="Check angle for new faces",
      default = True )      
    
    bpy.types.Scene.min_angle = bpy.props.FloatProperty(  
      name  = 'min_angle',  
      default  = radians(3),  
      subtype = 'ANGLE',  
      description = "minimal angle between edges" )  
      
    bpy.types.Scene.max_angle = bpy.props.FloatProperty(  
      name  = 'max_angle',  
      default  = radians(160),  
      subtype = 'ANGLE',  
      description = "max angle between edges" )  

    bpy.types.Scene.check_area = bpy.props.BoolProperty(
      name="check_area",
      description="Check area for new faces",
      default = False )

    bpy.types.Scene.min_area = bpy.props.FloatProperty(  
      name  = 'min_area',  
      default  = 0,
      min = 0,
      description = "min area for new face" )  
      
    bpy.types.Scene.max_area = bpy.props.FloatProperty(  
      name  = 'max_area',  
      default  = 10000,
      min = 0,      
      description = "max area for new face" )

    bpy.types.Scene.use_material = bpy.props.BoolProperty(
      name="use_material",
      description="Use material for new faces",
      default = False )      
   
    bpy.types.Scene.units_size = bpy.props.EnumProperty(items= (('0', 'm', 'meters'),    
                                                 ('1', 'cm', 'centimeters'),    
                                                 ('2', 'mm', 'millimeters')),                                                     
                                                 name = 'unit size')      
   
       
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        
        layout.label("Normal direction")
        layout.prop(scn,'normal_direction', expand=True)         
        
        layout.label("3 || 4")
        layout.prop(scn,'triangle_or_square', expand=True) 
        
        layout.prop(scn,'all_face_from_one_vert',text='All faces')  
        layout.prop(scn,'auto_select_next_vert',text='Auto select') 
        
        #layout.label("Angle")
        layout.prop(scn,'check_angle',text='Check angle')  
        row = layout.row(align=True)
        row.prop(scn,'min_angle',text='')
        row.prop(scn,'max_angle',text='')
        row = layout.row(align=True)
        layout.prop(scn,'check_area',text='Check area') 
        #row.prop(scn,'check_area',text='Check area') 
        layout.prop(scn,'units_size',expand=True)        
        row = layout.row(align=True)
        row.prop(scn,'min_area',text='')
        row.prop(scn,'max_area',text='')
        
        layout.prop(scn,'use_material',text='use_material')  
  

def get_intersection_vertex(x1,x2,x3,x4,y1,y2,y3,y4,z1,z2,z3,z4):
   #debug=True
   debug=False

   eps = 0.000001;  # Zero
   
   d =(x1-x2)*(y4-y3) - (y1-y2)*(x4-x3)
   da=(x1-x3)*(y4-y3) - (y1-y3)*(x4-x3)
   db=(x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)
  
   if abs(d)<eps:
     if debug: print('otrezki na paeallelnyh pryamyh')
     return None,None,None
   else:         
     ta=da/d
     tb=db/d    
     
     if (0<=ta) and (ta<=1) and (0<=tb) and (tb<=1):
           dotx=x1+ta*(x2-x1)
           doty=y1+ta*(y2-y1)
           dotz=z1+ta*(z2-z1) 
           return dotx,doty,dotz     
     else:
       if debug: print('otrezki ne peresekayutca')
       return None,None,None

   
def check_line_intersection(vert1,vert2,vert3,vert4): 
    #print('check_line_intersection')
    
    #debug=True
    debug=False 
   
    eps = 0.000001;   # Zero
   
   
    (x1,y1,z1)=vert1.co
    (x2,y2,z2)=vert2.co     
    (x3,y3,z3)=vert3.co 
    (x4,y4,z4)=vert4.co   

    (x1,y1,z1)=(round(x1,4),round(y1,4),round(z1,4))
    (x2,y2,z2)=(round(x2,4),round(y2,4),round(z2,4)) 
    (x3,y3,z3)=(round(x3,4),round(y3,4),round(z3,4))
    (x4,y4,z4)=(round(x4,4),round(y4,4),round(z4,4))
    
    
    a11=x1-x2
    a12=y1-y2
    a13=z1-z2
    a21=x3-x4
    a22=y3-y4
    a23=z3-z4
    a31=x1-x3
    a32=y1-y3
    a33=z1-z3

    opredelitel=a11*a22*a33 + a12*a23*a31 + a13*a21*a32 - a13*a22*a31 - a11*a23*a32 - a12*a21*a33                   
    next_face_flag=False
    
    #if opredelitel==0:         
    if abs(opredelitel)<eps:
                   
       dotx,doty,dotz=get_intersection_vertex(x1,x2,x3,x4,y1,y2,y3,y4,z1,z2,z3,z4)   
       if dotx==None:
         dotx,dotz,doty=get_intersection_vertex(x1,x2,x3,x4,z1,z2,z3,z4,y1,y2,y3,y4)
       if dotx==None:
         doty,dotz,dotx=get_intersection_vertex(y1,y2,y3,y4,z1,z2,z3,z4,x1,x2,x3,x4)               
                           
       if dotx!=None and doty!=None and dotz!=None:     
               
         (dotx,doty,dotz)=(round(dotx,4),round(doty,4),round(dotz,4))
         
         
         if dotx==x1 and doty==y1 and dotz==z1 :                 
           return next_face_flag  
         elif dotx==x2 and doty==y2 and dotz==z2:      
           return next_face_flag     
         elif dotx==x3 and doty==y3 and dotz==z3:       
           return next_face_flag  
         elif dotx==x4 and doty==y4 and dotz==z4:                   
           return next_face_flag     
         else:     
           #debug=True
           if debug: 
             print('tochka peresecheniya')     
             print(dotx,doty,dotz)           
              
           next_face_flag=True     
           return next_face_flag   
    return next_face_flag          
    
    
def check_face_and_dot(x,y,z,x1,y1,z1,x2,y2,z2,x3,y3,z3):
    #debug=True
    debug=False
    
    #print('check_face_and_dot')
    
    eps = 0.000001;   # Zero
   
    
    a11=x-x1 
    a12=y-y1         
    a13=z-z1         
    a21=x2-x1         
    a22=y2-y1         
    a23=z2-z1         
    a31=x3-x1 
    a32=y3-y1 
    a33=z3-z1    

    opredelitel=a11*a22*a33 + a12*a23*a31 + a13*a21*a32 - a13*a22*a31 - a11*a23*a32 - a12*a21*a33  
    
    if debug:
      print('opredelitel')                      
      print(opredelitel)         
   
    #if opredelitel==0:        
    if abs(opredelitel)<eps:
      return True
    return False  
    

def correct_normal(new_face,vert_sel,screen_pos,obj):
             #debug=True
             debug=False
             
             #print('correct_normal')
             
             bm = bmesh.from_edit_mesh(bpy.context.active_object.data) 
             for face in bm.faces: 
                face.select=False
             for edge in bm.edges: 
                edge.select=False   
             for vert in bm.verts: 
                vert.select=False
             
             new_face.select=True
             
             bpy.ops.mesh.flip_normals()    
             
             if debug: 
               print('new_face.normal')
               print(new_face.normal) 

             pnormal = obj.matrix_world.to_3x3() * new_face.normal
             
             if debug: 
               print('pnormal')
               print(pnormal)
               
             world_coordinate = obj.matrix_world * vert_sel.co
             
             if debug: 
               print('world_coordinate')
               print(world_coordinate)

             result_vector = screen_pos - world_coordinate
             
             if debug: 
               print('result_vector')
               print(result_vector)
             
             #dot_value = pnormal.dot(result_vector)                    
             dot_value = pnormal.dot(result_vector.normalized())        
             
             if debug: 
               print('dot_value')
               print(dot_value)
             
             # bpy.context.scene.normal_direction = пиктограмма в меню 0 и 1
   
             normal_direction=int(bpy.context.scene.normal_direction)            
                   
             if (dot_value<0 and normal_direction==0) or (dot_value>=0 and normal_direction>0):  
                if debug: print('flip normal') 
                bpy.ops.mesh.flip_normals()

                
def bad_angle(verts):            
             #debug=True
             debug=False
             
             #Pi=math.pi
             Pi=pi
             
             (vert_sel,vert2,vert3)=verts
             if debug:
               print("vert_sel")
               print("vert2")
               print("vert3")  
               print(vert_sel.co)
               print(vert2.co)
               print(vert3.co)           
         
             (x1,y1,z1)=vert_sel.co
             (x2,y2,z2)=vert2.co
             (x3,y3,z3)=vert3.co
             
             #Расчет углов треугольника
             vector1=mathutils.Vector((x2-x1,y2-y1,z2-z1))
             vector2=mathutils.Vector((x3-x1,y3-y1,z3-z1))
             vector3=mathutils.Vector((x3-x2,y3-y2,z3-z2))
             vector4=mathutils.Vector((x2-x3,y2-y3,z2-z3)) 
             
             try:
               angle1=vector1.angle(vector2)   
               angle2=vector2.angle(vector3)   
               #angle3=vector1.angle(vector3)  #Bad angle
               angle3=vector1.angle(vector4)   
             except:  
               if debug: print('don`t make face bad angle')
               return True
             
             '''
             min_radian=min_gradus*Pi/180
             max_radian=max_gradus*Pi/180
             '''
             
             angle1=round(angle1,3)
             angle2=round(angle2,3)
             angle3=round(angle3,3)
                    
             min_radian=round(bpy.context.scene.min_angle,3)
             max_radian=round(bpy.context.scene.max_angle,3)
             
             if int(bpy.context.scene.triangle_or_square):
               if debug:
                 print('angle1')
                 print(angle1*180/Pi)
                 print('angle2')
                 print(angle2*180/Pi)
                 print('angle3')
                 print(angle3*180/Pi)           
                 
                 print('min_radian')
                 print(min_radian)
                 print('max_radian')
                 print(max_radian)  
               
               if (angle1<min_radian or angle1>max_radian or (angle2+angle3)<min_radian or angle2>max_radian or angle3>max_radian):
                 if debug: print('don`t make face bad angle')
                 return True
             else:           
               if (angle1<min_radian or angle1>max_radian or angle2<min_radian or angle2>max_radian or angle3<min_radian or angle3>max_radian):
                 if debug: print('don`t make face bad angle')
                 return True
             
             return False

             
def bad_area(verts):
   
   (vert_sel,vert2,vert3)=verts
      
   (x1,y1,z1)=vert_sel.co
   (x2,y2,z2)=vert2.co
   (x3,y3,z3)=vert3.co 
   
   vector1=mathutils.Vector((x2-x1,y2-y1,z2-z1))
   vector2=mathutils.Vector((x3-x1,y3-y1,z3-z1))
   
   angle1=vector1.angle(vector2)  
   
   h=vector1.length*math.sin(angle1)
   S=0.5*vector2.length*h
   
   if int(bpy.context.scene.triangle_or_square):
     S=S*2   
   
   #scale_length=bpy.data.scenes["Scene"].unit_settings.scale_length
   units_size=int(bpy.context.scene.units_size)
   
   min_area=float(bpy.context.scene.min_area)
   max_area=float(bpy.context.scene.max_area)
   
   if units_size==0:
     #m2 -> cm2
     min_area=min_area*10000
     max_area=max_area*10000
   elif units_size==2:  
     #mm2 -> cm2
     min_area=min_area/100
     max_area=max_area/100  
   '''  
   elif units_size==1:
     #cm2 
     min_area=min_area
     max_area=max_area
   '''  
   
   if S<min_area or S>max_area:
     return True
   
   return False    

   
def check_face_verts_all_in(vert1,vert2,vert3,face):

  #print('check_face_verts_all_in')

  #debug=True
  debug=False  
  
  (x1,y1,z1)=vert1.co
  (x2,y2,z2)=vert2.co
  (x3,y3,z3)=vert3.co  
  
  verts_to_check=len(face.verts)
  i=0  
  while i < verts_to_check:   
    (x,y,z)=face.verts[i].co
    i=i+1        
    if debug: print(x,y,z)
    if not check_face_and_dot(x,y,z,x1,y1,z1,x2,y2,z2,x3,y3,z3):
      if debug: print("ne v odnoy ploskosti - proverka zakonchena")
      return False
    
  pr=1
  while pr<4:
    if debug:
      print('proeciya num')
      print(pr)
    
    if pr==1:
      if debug: print('x not good')
      A12=y2-y1
      B12=z1-z2
      C12=z2*y1-z1*y2
    if pr==2:
      if debug: print('y not good')
      A12=z2-z1
      B12=x1-x2
      C12=x2*z1-x1*z2
    if pr==3:
      if debug: print('z not good')
      A12=y2-y1
      B12=x1-x2
      C12=x2*y1-x1*y2
    
    if pr==1:
      if debug: print('x not good')
      A13=y3-y1
      B13=z1-z3
      C13=z3*y1-z1*y3
    if pr==2:
      if debug: print('y not good')
      A13=z3-z1
      B13=x1-x3
      C13=x3*z1-x1*z3
    if pr==3:
      if debug: print('z not good')
      A13=y3-y1
      B13=x1-x3
      C13=x3*y1-x1*y3   
     
    if pr==1:
      if debug: print('x not good')
      A23=y3-y2
      B23=z2-z3
      C23=z3*y2-z2*y3
    if pr==2:
      if debug: print('y not good')
      A23=z3-z2
      B23=x2-x3
      C23=x3*z2-x2*z3
    if pr==3:
      if debug: print('z not good')
      A23=y3-y2
      B23=x2-x3
      C23=x3*y2-x2*y3    
    
    
    if pr==1:      
      sign12=A12*z3+B12*y3+C12
      sign13=A13*z2+B13*y2+C13
      sign23=A23*z1+B23*y1+C23
    if pr==2:      
      sign12=A12*x3+B12*z3+C12
      sign13=A13*x2+B13*z2+C13
      sign23=A23*x1+B23*z1+C23  
    if pr==3:      
      sign12=A12*x3+B12*y3+C12
      sign13=A13*x2+B13*y2+C13
      sign23=A23*x1+B23*y1+C23
      
 
    i=0  
    while i < verts_to_check:   
      (x,y,z)=face.verts[i].co
      i=i+1        
      if debug: print(x,y,z)
      
      if pr==1:    
        sign1=A12*z+B12*y+C12
        sign2=A13*z+B13*y+C13
        sign3=A23*z+B23*y+C23
      
      if pr==2:    
        sign1=A12*x+B12*z+C12
        sign2=A13*x+B13*z+C13
        sign3=A23*x+B23*z+C23
      
      if pr==3:    
        sign1=A12*x+B12*y+C12
        sign2=A13*x+B13*y+C13
        sign3=A23*x+B23*y+C23 

      
      if ((sign12<=0 and sign1<=0) or (sign12>=0 and sign1>=0)) and ((sign13<=0 and sign2<=0) or (sign13>=0 and sign2>=0)) and ((sign23<=0 and sign3<=0) or (sign23>=0 and sign3>=0)):
        if debug: print('vse znaki sovpali tochka vnutri libo na linii')
      else:        
        if debug: print('znaki NE sovpali tochka vneshnaya')
        return False  
    pr=pr+1
    
  return True


def check_face_verts_all_out(vert1,vert2,vert3,face):
  #print('check_face_verts_all_out')
  
  #debug=True
  debug=False  
  if len(face.verts) > 3:
    return False
  
  verts=[vert1,vert2,vert3]
   
  (x1,y1,z1)=vert1.co
  (x2,y2,z2)=vert2.co
  (x3,y3,z3)=vert3.co  
  
  verts_to_check=len(face.verts)
  i=0  
  while i < verts_to_check:   
    (x,y,z)=face.verts[i].co
    i=i+1        
    if debug: print(x,y,z)
    if not check_face_and_dot(x,y,z,x1,y1,z1,x2,y2,z2,x3,y3,z3):
      if debug: print("ne v odnoy ploskosti - proverka zakonchena")
      return False
 

  (x1,y1,z1)=face.verts[0].co
  (x2,y2,z2)=face.verts[1].co
  (x3,y3,z3)=face.verts[2].co 
  
  pr=1
  while pr<4:
  
    if debug:  
      print('proeciya num')  
      print(pr)  
  
    if pr==1:
      A12=y2-y1
      B12=z1-z2
      C12=z2*y1-z1*y2
    if pr==2:
      A12=z2-z1
      B12=x1-x2
      C12=x2*z1-x1*z2
    if pr==3:
      A12=y2-y1
      B12=x1-x2
      C12=x2*y1-x1*y2
    
    if pr==1:
      A13=y3-y1
      B13=z1-z3
      C13=z3*y1-z1*y3
    if pr==2:
      A13=z3-z1
      B13=x1-x3
      C13=x3*z1-x1*z3
    if pr==3:
      A13=y3-y1
      B13=x1-x3
      C13=x3*y1-x1*y3   
     
    if pr==1:
      A23=y3-y2
      B23=z2-z3
      C23=z3*y2-z2*y3
    if pr==2:
      A23=z3-z2
      B23=x2-x3
      C23=x3*z2-x2*z3
    if pr==3:
      A23=y3-y2
      B23=x2-x3
      C23=x3*y2-x2*y3    
    
    
    #verts_to_check=len(face.verts)
    verts_to_check=3
    
    if pr==1:
      sign12=A12*z3+B12*y3+C12
      sign13=A13*z2+B13*y2+C13
      sign23=A23*z1+B23*y1+C23
    if pr==2:
      sign12=A12*x3+B12*z3+C12
      sign13=A13*x2+B13*z2+C13
      sign23=A23*x1+B23*z1+C23  
    if pr==3:
      sign12=A12*x3+B12*y3+C12
      sign13=A13*x2+B13*y2+C13
      sign23=A23*x1+B23*y1+C23
    
  
    i=0  
    while i < verts_to_check:   
      (x,y,z)=verts[i].co
      i=i+1        
      if debug: print(x,y,z)          
      
      if pr==1:    
        sign1=A12*z+B12*y+C12
        sign2=A13*z+B13*y+C13
        sign3=A23*z+B23*y+C23
      
      if pr==2:    
        sign1=A12*x+B12*z+C12
        sign2=A13*x+B13*z+C13
        sign3=A23*x+B23*z+C23
      
      if pr==3:    
        sign1=A12*x+B12*y+C12
        sign2=A13*x+B13*y+C13
        sign3=A23*x+B23*y+C23 
      
      if ((sign12<=0 and sign1<=0) or (sign12>=0 and sign1>=0)) and ((sign13<=0 and sign2<=0) or (sign13>=0 and sign2>=0)) and ((sign23<=0 and sign3<=0) or (sign23>=0 and sign3>=0)):
        if debug: print('vse znaki sovpali tochka vnutri libo na linii')
      else:
        if debug: print('znaki NE sovpali tochka vneshnaya')
        return False      
    pr=pr+1
  
  return True

 
def location_3d_to_region_2d_world_correct(region, rv3d, coord, context, default=None):
    """
    Return the *region* relative 2d location of a 3d position.

    :arg region: region of the 3D viewport, typically bpy.context.region.
    :type region: :class:`bpy.types.Region`
    :arg rv3d: 3D region data, typically bpy.context.space_data.region_3d.
    :type rv3d: :class:`bpy.types.RegionView3D`
    :arg coord: 3d worldspace location.
    :type coord: 3d vector
    :arg default: Return this value if ``coord``
       is behind the origin of a perspective view.
    :return: 2d location
    :rtype: :class:`mathutils.Vector` or ``default`` argument.
    """
    
    '''
    perspective_matrix
    Current perspective matrix (window_matrix * view_matrix)
    '''
    
    from mathutils import Vector

    obj = context.active_object 
    correct_vector=obj.matrix_world * Vector((coord[0], coord[1], coord[2], 1.0))
    prj = rv3d.perspective_matrix*correct_vector
    
    if prj.w > 0.0:
        width_half = region.width / 2.0
        height_half = region.height / 2.0
        
        return Vector((width_half + width_half * (prj.x / prj.w),
                       height_half + height_half * (prj.y / prj.w),
                       ))
    else:
        return default

 
def get_nearest_vert(verts,context,event): 
    region = context.region
    rv3d =context.space_data.region_3d  

    mouse_pos = mathutils.Vector([event.mouse_region_x, event.mouse_region_y]) 
    
    min_dist=0
    vert_minimal=None
    
    for vert in verts:         
      vert_pos=location_3d_to_region_2d_world_correct(region, rv3d, vert.co, context) 
      if vert_pos is not None:
        dist = (mouse_pos - vert_pos).length     
        if min_dist==0 or min_dist>dist:    
          min_dist=dist    
          vert_minimal = vert 

    return vert_minimal          
         
 
def select_next_vert(verts,new_face,context,event):
    #print('select_next_vert')
    
    #debug=True
    debug=False   
    
    region = context.region
    rv3d =context.space_data.region_3d  
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)     
    
    best_verts=[]

    for vert in verts:
      if len(vert.link_edges)>=2:        
        for edge in vert.link_edges:
          if new_face: 
            if edge not in new_face.edges:             
              best_verts.append(vert)
              break
          else:
            best_verts.append(vert)
            break
   
    mouse_pos = mathutils.Vector([event.mouse_region_x, event.mouse_region_y]) 
           
    #region.width  величины постоянные и зависят от размера вьюпорта
    #region.height
           
    #screen_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))
    
    vert_minimal=get_nearest_vert(best_verts,context,event)
    
    for face in bm.faces: 
       face.select=False
    for edge in bm.edges: 
       edge.select=False   
    for vert in bm.verts: 
       vert.select=False
   
    if vert_minimal is not None:      
      vert_minimal.select=True
      
    return     
       
       
def make_face(bm,verts,screen_pos,obj,context,event):    
             
             #print('make_face')

             #debug=True
             debug=False         
             
             (vert_sel,vert2,vert3)=verts
             
             if bpy.context.scene.check_angle:
               if bad_angle(verts): return False            
             
             if bpy.context.scene.check_area:
               if bad_area(verts): return False
             
             
             if int(bpy.context.scene.triangle_or_square):
               
               (x1,y1,z1)=vert_sel.co
               (x2,y2,z2)=vert2.co
               (x3,y3,z3)=vert3.co
                              
               vector1=mathutils.Vector((x2-x1,y2-y1,z2-z1))
               vector2=mathutils.Vector((x3-x1,y3-y1,z3-z1))
                              
               dot=vert_sel.co+vector1
               dot=dot+vector2
               
               (x,y,z)=dot
               
               dot=bm.verts.new(dot) 
                 
               #verts=verts+[dot]   
               verts=[vert_sel,vert2,dot,vert3]   

             new_face=bm.faces.new(verts)         
             if debug: print("face created, terminate")             
              
             new_face.select=True         
             
             correct_normal(new_face,vert_sel,screen_pos,obj)      
             
             if int(bpy.context.scene.use_material):
               mat_index = None
               smooth = False
               for vert in  verts:
                 for face in vert.link_faces: 
                   if face != new_face:                 
                     mat_index = face.material_index
                     #print('mat_index')
                     #print(mat_index)
                     smooth = face.smooth 
                     if mat_index is not None: 
                      new_face.material_index = mat_index
                      new_face.smooth = smooth                    
                      break
                 if mat_index is not None: break   
             
             
             if bm.select_mode=={'EDGE'}:
               best_vert1=get_nearest_vert(verts,context,event)
               verts.remove(best_vert1)
               best_vert2=get_nearest_vert(verts,context,event)
             
               for face in bm.faces: 
                  face.select=False
               for edge in bm.edges: 
                  edge.select=False   
               for vert in bm.verts: 
                  vert.select=False
             
               for edge in best_vert1.link_edges:
                 if edge in best_vert2.link_edges:
                   edge.select=True
                   break
             else:      
               if bpy.context.scene.auto_select_next_vert and not bpy.context.scene.all_face_from_one_vert:
                 select_next_vert(verts,new_face,context,event)
             
             return True
                

def face_from_vertex(bm, vert_sel, vert_sel2, edge_sel, context, event, self):   
    #print('face_from_vertex') 
    
    #debug=True
    debug=False 
    
    vert_sel_def,vert_sel2_def=vert_sel, vert_sel2
    
    from mathutils import Vector    
    obj = context.active_object         
    region = context.region
    region_3d = context.space_data.region_3d
    rv3d =context.space_data.region_3d  
    
    screen_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))
    
    '''
    if debug: 
      print('screen_pos')
      print(screen_pos)
    '''
    
    edges  = vert_sel.link_edges  
    if vert_sel2 is not None:
      edges2 = vert_sel2.link_edges    
      
      if len(edges)<=1:
        print('len <=1')
        vert_sel=vert_sel2
        edges = edges2
      elif len(edges2)>1: 
        min_dist=0    
        mouse_pos = mathutils.Vector([event.mouse_region_x, event.mouse_region_y])        
        for vert in [vert_sel,vert_sel2]:
          vert_pos=location_3d_to_region_2d_world_correct(region, rv3d, vert.co.copy(),context)              
          
          dist = (mouse_pos - vert_pos).length 
          
          if min_dist==0 or min_dist>dist:
            min_dist=dist
            vert_minimal = vert
         
        vert_sel=vert_minimal
        edges  = vert_sel.link_edges  

    if debug: 
      print('All edges')
      print(len(edges))
    
    break_flag_face_created=False
    verts=None    
    edge_number=0
    
    make_face_hash={} 
    proxod_num=0
    
    edges_len=len(edges)-1
    edges_i=0
    edges_j=0
    
    while edges_i < edges_len:
      
      edges_j=edges_i+1     
      edge=edges[edges_i]
      
      while edges_j <= edges_len:              
        edge2=edges[edges_j]      
        
        next_face_flag=False
        
        if edge2 == edge: 
          print("continue, edge2=edge")
          edges_j=edges_j+1
          continue
          
        continue_flag=False
        
        for check_face in edge.link_faces:    
          print(check_face)        
          print("face index: "+str(check_face.index))
          if check_face.index==-1:
            print("fake face continue...")            
            continue          
          
          if edge2 in check_face.edges:            
            continue_flag=True
          
        if continue_flag:
          print("continue face exist nothing to do")
          next_face_flag=True 
          edges_j=edges_j+1
          continue
        else:  
           vert2=None
           vert3=None
           
           for vert in edge.verts:
             if vert != vert_sel:
               if vert.co != vert_sel.co:
                 vert2=vert               
                 break
               self.report({'ERROR'}, "Несколько совпадающих вершин в меше\n Some verts are same in that mesh")
           
           for vert in edge2.verts:
             if vert != vert_sel:
               if vert.co != vert_sel.co:
                 vert3=vert
                 break                 
               self.report({'ERROR'}, "Несколько совпадающих вершин в меше\n Some verts are same in that mesh")
           if vert2 is None or vert3 is None:
               edges_j=edges_j+1
               continue
           
           verts=[vert_sel,vert2,vert3]                      
           
           #debug=True
           if debug: 
             print("create new face with verts:")
             print(vert_sel.co)
             print(vert2.co)
             print(vert3.co)                    
           #debut=False
           
           if bpy.context.scene.check_angle:
             if bad_angle(verts):
               if debug: print("plohie ugli - sleduyushiy poligon")
               edges_j=edges_j+1
               continue         
           debug=False
           
           check_faces={}
           
           for face in vert_sel.link_faces:
             check_faces[face]=1
           for face in vert2.link_faces:
             check_faces[face]=1
           for face in vert3.link_faces:
             check_faces[face]=1
             
           if debug: 
             print("Total faces to check")
             print(len(check_faces))
             print(check_faces)
           
           if len(check_faces)==0:
             if not next_face_flag:
               if verts:
                 make_face_hash[proxod_num]=verts
                 proxod_num=proxod_num+1
                 edges_j=edges_j+1
                 continue
           for face in check_faces:
             if debug:
               print('kol-vo tochek u proveryaemogo poligona face.verts')
               print(len(face.verts))
               
             if check_face_verts_all_in(vert_sel,vert2,vert3,face):
               next_face_flag=True
               break  

             if check_face_verts_all_out(vert_sel,vert2,vert3,face):
               next_face_flag=True
               break   
             
             verts_to_check=len(face.verts)-1
             #debug=True
             if debug:
               print('next_face_flag')
               print(next_face_flag)               
               print('Nachinaem proverku na peresechenie')               
               print('verts_to_check')
               print(verts_to_check)
             #debug=False
             i=0
             j=0
             while i < verts_to_check:
               if next_face_flag:
                 break
               (ix,iy,iz)=face.verts[i].co
               j=i+1       
               while j <= verts_to_check:
                 (jx,jy,jz)=face.verts[j].co                                  
                 next_face_flag=check_line_intersection(vert_sel,vert2,face.verts[i],face.verts[j])             
               
                 if next_face_flag: 
                
                   break  
                 next_face_flag=check_line_intersection(vert_sel,vert3,face.verts[i],face.verts[j])             
                
                 if next_face_flag:
                 
                   break  
                 next_face_flag=check_line_intersection(vert2,vert3,face.verts[i],face.verts[j])             
                 
                 if next_face_flag: 
                  
                   break
                   
                 j=j+1  
               i=i+1
               
             if next_face_flag:
               break  
           
           if not next_face_flag: 
             if verts: 
               make_face_hash[proxod_num]=verts               
               proxod_num=proxod_num+1
               edges_j=edges_j+1
               continue
              
        edges_j=edges_j+1    
      edges_i=edges_i+1
      
    #print(make_face_hash)
    min_dist=0
    best_proxod_num=0
    all_verts=[]
    make_face_nearest=True
    
    all_distances={} 
    
    if bpy.context.scene.all_face_from_one_vert:
      make_face_nearest=False
    for proxod_num in make_face_hash:
      verts=make_face_hash[proxod_num]
      all_verts+=verts
      if make_face_nearest:
        dist=0
        for vert in verts:
          vert_co_in_world=obj.matrix_world * vert.co
          dist = dist+(screen_pos - vert_co_in_world).length
          all_distances[proxod_num]=dist
        
        if min_dist==0 or min_dist>dist:  
          min_dist=dist  
          best_proxod_num = proxod_num          
      else: 
        if vert_sel2_def is not None:
          if vert_sel_def in verts and vert_sel2_def in verts:  
            make_face(bm,verts,screen_pos,obj,context,event)
        else:
          make_face(bm,verts,screen_pos,obj,context,event)
          
    if make_face_nearest and make_face_hash:
      for (key,distance) in sorted(all_distances.items(),key=lambda t: t[1]):
        verts=make_face_hash[key]
        if vert_sel2_def is not None:
          if vert_sel_def in verts and vert_sel2_def in verts: 
            print('vert_sel and vert_sel2')
            print(vert_sel.co)
            print(vert_sel2.co)
          
            if make_face(bm,verts,screen_pos,obj,context,event):
              break
        else:
          if make_face(bm,verts,screen_pos,obj,context,event):
            break
    elif make_face_hash:
      if bpy.context.scene.auto_select_next_vert:
        print('Try to select best vert from all verts')
        select_next_vert(all_verts,None,context,event)
    
    if not make_face_hash: bpy.ops.object.dialog_error_message('INVOKE_DEFAULT')
    
    # toggle mode, to force correct drawing  
    bpy.ops.object.mode_set(mode='OBJECT') 
    bpy.ops.object.mode_set(mode='EDIT')   
    
    return


class SmartF(bpy.types.Operator):    
    bl_idname = "mesh.smartf"    
    bl_label = "Make Edge/Face"
    bl_description = "Smart and fast making face"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # check we are in mesh editmode
        obj = context.active_object
        return(obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

    def invoke(self, context, event):
        # toggle mode, to force correct drawing                   
        bpy.ops.object.mode_set(mode='OBJECT')      
        bpy.ops.object.mode_set(mode='EDIT')             
    
        bm = bmesh.from_edit_mesh(context.active_object.data)
        sel = [v for v in bm.verts if v.select]
        if len(sel) > 2:
            # original 'Make Edge/Face' behaviour with little changes
            try:
              region = context.region
              rv3d =context.space_data.region_3d  
              obj = context.active_object   
              
              bpy.ops.mesh.edge_face_add('INVOKE_DEFAULT')
                  
              bm.faces.ensure_lookup_table()
              
              new_face_index=len(bm.faces)-1 
              new_face=bm.faces[new_face_index]    
              vert_sel=new_face.verts[0]    
               
              screen_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))    
              correct_normal(new_face,vert_sel,screen_pos,obj)  
            except:
                return {'CANCELLED'}
        elif len(sel) == 1:            
            face_from_vertex(bm, sel[0], None, None, context, event, self)            
        elif len(sel) == 2:
            edges_sel = [ed for ed in bm.edges if ed.select]
            if len(edges_sel) != 1:
                # 2 vertices selected, but not on the same edge
                bpy.ops.mesh.edge_face_add()
            else:  
                # 0 - tris  1 - quad
                bpy.context.scene.triangle_or_square="1"
                #if int(bpy.context.scene.triangle_or_square): 
                vert_sel1=edges_sel[0].verts[0]  
                vert_sel2=edges_sel[0].verts[1]  
                face_from_vertex(bm, vert_sel1, vert_sel2, edges_sel[0], context, event, self)  
                '''  
                else:  
                  bpy.ops.mesh.edge_face_add()
                '''
        return {'FINISHED'}

  
# registration
addon_keymaps = []

def register():    
    bpy.utils.register_class(SmartF)
    bpy.utils.register_class(SmartFMenu)       
    bpy.utils.register_class(DialogErrorMessage)
    
    # add keymap entry
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')    
    kmi = km.keymap_items.new("mesh.smartf", 'F', 'PRESS')
    addon_keymaps.append((km, kmi))
    

def unregister():    
    # remove keymap entry   
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)   
 
    addon_keymaps.clear()  
    
    bpy.utils.unregister_class(DialogErrorMessage)
    bpy.utils.unregister_class(SmartFMenu)    
    bpy.utils.unregister_class(SmartF)   
   
  
if __name__ == "__main__":
    register()