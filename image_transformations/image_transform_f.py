import cv2
import numpy as np


# Class changes to incorp from other classes.y


class Image_Transform(object):

    def __init__(self):
        self.array_points_fire_img = []
        self.array_points_vertical_img = []

        self.fire_image_open = None
        self.vertical_image_open = None

        self.transform_matrix = None

    def get_points_fire_img(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDBLCLK:
            fire_image_points = (x, y)
            cv2.circle(self.fire_image_open, fire_image_points, 5, (0, 0, 255), -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(self.fire_image_open, str(len(self.array_points_fire_img)), fire_image_points, font, 0.8,
                        (0, 0, 255), 1,
                        cv2.LINE_AA)

            self.array_points_fire_img.append((x, y))

            print(self.array_points_fire_img)

    def get_points_vertical_img(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDBLCLK:
            vertical_image_points = (x, y)
            cv2.circle(self.vertical_image_open, vertical_image_points, 5, (0, 0, 255), -1)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(self.vertical_image_open, str(len(self.array_points_vertical_img)), vertical_image_points, font,
                        0.8,
                        (0, 0, 255), 1, cv2.LINE_AA)
            self.array_points_vertical_img.append((x, y))

            print(self.array_points_vertical_img)

    def generate_transform_matrix(self):

        arraypoints_fire = np.array(self.array_points_fire_img)
        arraypoints_vertical = np.array(self.array_points_vertical_img)

        h, status = cv2.findHomography(arraypoints_fire, arraypoints_vertical)

        warped_image = cv2.warpPerspective(self.fire_image_open, h,
                                           (self.vertical_image_open.shape[1], self.vertical_image_open.shape[0]))

        cv2.namedWindow('Warped Source Image', cv2.WINDOW_NORMAL)
        cv2.imshow("Warped Source Image", warped_image)

        cv2.namedWindow('Overlay', cv2.WINDOW_NORMAL)
        overlay_image = cv2.addWeighted(self.vertical_image_open, 0.3, warped_image, 0.8, 0)
        cv2.imshow('Overlay', overlay_image)

        self.transform_matrix = h

    def load_points_from_file(self):

        # Load segmentation points from original image

        if self.transform_matrix is not None:

            points_file = input("File with points to convert > ")
            try:
                l = np.load(points_file)

                pretty_points = []
                for item in l:
                    for i in item:
                        for x in i:
                            pretty_points.append([x[0], x[1]])

                self.convert_points_to_vertical_image(l)

                # self.convert_points_to_georef(vertical_points_convertion)

            except IOError:
                print("File not found, try again")
                self.load_points_from_file()
        else:
            print("Need to transform the image first!")
            return

    def convert_points_to_vertical_image(self, l):

        # Use generated transform matrix to convert points between images

        final_points = []

        for x in range(len(l)):

            pts = np.array(l[x], dtype="float32")

            # Transform to vertcal
            converted_points = cv2.perspectiveTransform(pts, self.transform_matrix)

            # Transform to georef
            final_polygon_points = self.convert_points_to_georef(converted_points)

            # Save points
            final_points.append(final_polygon_points)

        print(final_points)

        np.save("converted_TRY", final_points)



    def convert_points_to_georef(self, vertical_points_convertion):

        # Linear Regression Model to convert points to GeoRef

        # georef_x_min = float(input("Minimum x value for Image Georef system > "))
        # georef_x_max = float(input("Maximum x value for Image Georef system > "))
        # georef_y_min = float(input("Minimum y value for Image Georef system > "))
        # georef_y_max = float(input("Maximum y value for Image Georef system > "))

        # Pre-defined values for our vertical image WGS

        georef_x_min = 615202.199
        georef_x_max = 616268.574
        georef_y_min = 4583991.175
        georef_y_max = 4582453.191

        original_y_max, original_x_max, channels = self.vertical_image_open.shape

        # Convert x point
        m_x = (georef_x_max - georef_x_min) / original_x_max

        # Convert y point
        m_y = (georef_y_max - georef_y_min) / original_y_max

        full_converted_points = []

        for abc in vertical_points_convertion:
            for cba in abc:
                my_points = [(m_x * cba[0]) + georef_x_min, (m_y * cba[1]) + georef_y_min]
                full_converted_points.append(my_points)

        return full_converted_points

    def main(self):

        self.fire_image_open = cv2.imread("Images/img1.jpg")
        clone_fire = self.fire_image_open.copy()
        cv2.namedWindow("FireImage", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("FireImage", self.get_points_fire_img)

        self.vertical_image_open = cv2.imread("Images/warp8k.tif")
        clone_vertical = self.vertical_image_open.copy()
        cv2.namedWindow("VerticalImage", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("VerticalImage", self.get_points_vertical_img)

        while True:
            cv2.imshow("FireImage", self.fire_image_open)
            cv2.imshow("VerticalImage", self.vertical_image_open)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("r"):
                print(">> ... RESET POINTS ...")
                self.fire_image_open = clone_fire.copy()
                self.vertical_image_open = clone_vertical.copy()
                self.array_points_fire_img = []
                self.array_points_vertical_img = []
                self.transform_matrix = None

            if key == ord("t"):

                print(">> ... Generate Transform matrix ...")

                if len(self.array_points_fire_img) == len(self.array_points_vertical_img) and len(
                        self.array_points_vertical_img) > 3:

                    self.generate_transform_matrix()
                else:
                    print(">> NUMBER OF POINTS NOT EQUAL, TRY AGAIN")
                    print(">> ... RESET POINTS ...")
                    self.fire_image_open = clone_fire.copy()
                    self.vertical_image_open = clone_vertical.copy()
                    self.array_points_fire_img = []
                    self.array_points_vertical_img = []
                    self.transform_matrix = None

            if key == ord("\r"):
                self.load_points_from_file()

            if key == ord("q"):
                break


if __name__ == "__main__":
    Image_Transform().main()
