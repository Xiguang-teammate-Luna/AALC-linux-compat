"""Adapt the configured second-system and avoid invalid fusion clicks."""


def not_enough_gifts(texts):
    text = ''.join(texts or ()).replace(' ', '')
    return '无法合成' in text and ('至少2' in text or '至少两' in text)


def install():
    from module.automation import auto
    from module.ocr import ocr
    from tasks.mirror.in_shop import Shop

    original_init = Shop.__init__

    def init(self, team_setting):
        original_init(self, team_setting)
        # TeamSetting declares these values as integers, while two upstream
        # branches check them with `is True`. Do not change the saved config.
        self.second_system_action = [bool(value) for value in self.second_system_action]

    Shop.__init__ = init

    original_fuse_system = Shop.fuse_system_gifts

    def fuse_system_gifts(self):
        original_click = auto.click_element
        had_override = 'click_element' in vars(auto)

        def click(target, *args, **kwargs):
            if target == 'mirror/shop/enhance_and_fuse_and_sell_confirm_assets.png':
                image = auto.take_screenshot()
                if image is not None:
                    toast = image.crop((int(image.width * .7), 0, image.width, int(image.height * .2)))
                    if not_enough_gifts(ocr.run(toast).txts):
                        return False
            return original_click(target, *args, **kwargs)

        auto.click_element = click
        try:
            return original_fuse_system(self)
        finally:
            if had_override:
                auto.click_element = original_click
            else:
                del auto.click_element

    Shop.fuse_system_gifts = fuse_system_gifts
